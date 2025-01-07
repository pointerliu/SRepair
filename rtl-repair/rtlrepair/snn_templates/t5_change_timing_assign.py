# Copyright 2022 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>
from typing import List

from rtlrepair.analysis import AnalysisResults, VarInfo
from rtlrepair.snn import SNNTemplate
from rtlrepair.snn_templates.utils import collect_blocks, get_lhs_width, \
    get_rhs_vars, convert_expr2net, CollectUtils
from rtlrepair.utils import Namespace
import pyverilog.vparser.ast as vast
from rtlrepair.visitor import template_guard

_synth_var_prefix = "__synth_"
_synth_change_prefix = "__synth_change_"


def t5_change_timing_assign(ast: vast.Source, analysis: AnalysisResults, bound_arch=[]):
    namespace = Namespace(ast)
    cu = collect_blocks(ast)
    assignment, blocking_assignment, nonblocking_assignment, cond_vars = cu.assignment, cu.blocking_assignment, cu.nonblocking_assignment, cu.cond_vars
    repl = ChangeTiming(cu, analysis.vars, analysis.widths, bound_arch)
    repl.apply(namespace, ast)


def _make_wire(name: str, width: int) -> vast.Decl:
    assert width >= 1
    width_node = None if width == 1 else vast.Width(vast.IntConst(str(width - 1)), vast.IntConst("0"))
    return vast.Decl((
        vast.Wire(name, width=width_node),
    ))


def _make_my_reg(name: str, width: int) -> vast.Decl:
    assert width >= 1
    width_node = None if width == 1 else vast.Width(vast.IntConst(str(width - 1)), vast.IntConst("0"))
    return vast.Decl((
        vast.Reg(name, width=width_node),
        # vast.Assign(
        #     left=vast.Lvalue(vast.Identifier(name)),
        #     right=vast.Rvalue(vast.IntConst(value='1'))
        # )
    ))


def _op_execute(op: vast.Node, x0: vast.Node, x1: vast.Node):
    if op is vast.Plus:
        return vast.Plus(x0, x1)
    elif op is vast.Minus:
        return vast.Minus(x0, x1)
    elif op is vast.Unot:
        return vast.Unot(x0)
    elif op is vast.And:
        return vast.And(x0, x1)
    elif op is vast.Or:
        return vast.Or(x0, x1)
    elif op is vast.Sll:
        return vast.Sll(x0, x1)
    elif op is vast.Srl:
        return vast.Srl(x0, x1)
    # Logic op
    # vast.Land,
    # vast.Lor,
    # vast.Eq,
    # vast.NotEq,
    # vast.Ulnot,
    elif op is vast.Land:
        return vast.Land(x0, x1)
    elif op is vast.Lor:
        return vast.Lor(x0, x1)
    elif op is vast.Eq:
        return vast.Eq(x0, x1)
    elif op is vast.NotEq:
        return vast.NotEq(x0, x1)
    elif op is vast.Ulnot:
        return vast.Ulnot(x0)
    elif op is vast.IntConst:
        return vast.IntConst(x0)
    elif op is vast.LessEq:
        return vast.LessEq(x0, x1)
    elif op == 'identity':
        return x0
    else:
        raise NotImplementedError(f'Unsupported operator {op} executing')


class ChangeTiming(SNNTemplate):
    def __init__(
            self,
            cu: CollectUtils,
            vars: dict[str, VarInfo],
            widths: dict[vast.Node, int],
            bound_arch: List = []
    ):
        super().__init__(cu, vars, widths, bound_arch=bound_arch)

        # SS
        self.decl_regs = []
        self.decl_always = []
        self.sense_list = []

    def _declare_synth_my_regs(self):
        return [_make_my_reg(name, width) for name, width in self.decl_regs]

    def apply(self, namespace: Namespace, ast: vast.Source):
        """ warn: modified in place! """
        # reset variables
        self.changed = []
        self.synth_vars = []
        self._namespace = namespace
        namespace.new_name(_synth_change_prefix + self.name)
        namespace.new_name(_synth_var_prefix + self.name)
        # visit AST
        self.visit(ast)

        assign_decls = self._declare_synth_assign()
        mod_def: vast.ModuleDef = ast.description.definitions[0]
        mod_def.items = tuple(assign_decls + list(mod_def.items))

        mod_def: vast.ModuleDef = ast.description.definitions[0]
        mod_def.items = tuple(self.decl_always + list(mod_def.items))

        wire_decls = self._declare_synth_wires()
        mod_def: vast.ModuleDef = ast.description.definitions[0]
        mod_def.items = tuple(wire_decls + list(mod_def.items))

        # declare synthesis vars
        decls = self._declare_synth_regs()
        mod_def: vast.ModuleDef = ast.description.definitions[0]
        mod_def.items = tuple(decls + list(mod_def.items))

        # declare synthesis vars
        decls = self._declare_synth_my_regs()
        mod_def: vast.ModuleDef = ast.description.definitions[0]
        mod_def.items = tuple(decls + list(mod_def.items))

    def get_ops_at(self, l: int, i: int):
        if f'{l}_{i}' not in self.ops_map:
            if self._cond_ops:
                return self.default_cond_ops
            return self.default_ops
        return self.ops_map[f'{l}_{i}']

    def _gen_reg_decl(self, name: str, width: int):
        name: str = self._namespace.new_name(name + '_reg')
        self.decl_regs.append((name, width))
        return vast.Identifier(name)

    def gen_always(self, lhs_bv: int, in_vars: List[vast.Node], l_var: vast.Node, r_var: vast.Rvalue, inplace: bool = False):
        if not inplace:
            reg_o = self._gen_reg_decl(f'reg_o_{self.namespace_id}', lhs_bv)
        else:
            reg_o = l_var
        self.namespace_id += 1
        clk = None
        for v in self.vars:
            if self.vars[v].is_clock:
                clk = vast.Identifier(name=v)
                break
        if clk is None:
            if len(self.sense_list) == 0:
                return reg_o
            else:
                clk = vast.Identifier(name=self.sense_list[0])

        self._bv = 1

        cond_vars = []
        for v in self.vars:
            if self.vars[v].width == 1 and self.vars[v].is_input and not self.vars[v].is_clock:
                cond_vars.append(vast.Identifier(name=v))
        cond_vars = list(set(cond_vars + in_vars))

        _, rhs_tree = self.get_rhs_tree(r_var.var)
        expr_net_mapping = convert_expr2net(r_var.var, len(rhs_tree))
        nodes_num = self.infer_arch(expr_net_mapping)

        snn_cond1 = self.build_snn(nodes_num=nodes_num, in_vars=cond_vars, expr_net_mapping=expr_net_mapping)
        snn_cond2 = self.build_snn(nodes_num=nodes_num, in_vars=cond_vars, expr_net_mapping=expr_net_mapping)
        snn_blk1 = vast.IntConst(value='0')
        self._bv = lhs_bv
        snn_blk2 = self.build_snn(nodes_num=nodes_num, in_vars=in_vars, expr_net_mapping=None)
        aws = vast.Always(sens_list=vast.SensList(list=[
            vast.Sens(sig=clk, type='posedge')
        ]), statement=vast.Block(statements=[
            vast.IfStatement(
                cond=snn_cond1,
                true_statement=vast.NonblockingSubstitution(
                    left=reg_o,
                    right=snn_blk1
                ),
                false_statement=vast.IfStatement(
                    cond=snn_cond2,
                    true_statement=vast.NonblockingSubstitution(
                        left=reg_o,
                        right=snn_blk2
                    ),
                    false_statement=None
                )
            )
        ]))

        self.decl_always.append(aws)

        return reg_o

    @template_guard
    def visit_Assign(self, node: vast.Assign):
        if self._in_gen_blk:
            return node
        # if node.left.var.name != 'out_ready':
        #     return node

        bow = get_lhs_width(node.left, self.vars)
        if bow >= 256:
            return node

        r_vars = [v for v in get_rhs_vars(node.right)]
        new_reg_var = self.gen_always(get_lhs_width(node.left, self.vars), r_vars, node.left, node.right)
        # node.right = self.make_change(new_reg_var, node.right)
        node.right = new_reg_var
        return node

    @template_guard
    def visit_BlockingSubstitution(self, node: vast.BlockingSubstitution):
        if self._in_gen_blk:
            return node
        # if node.left.var.name != 'counter_out':
        #     return node

        bow = get_lhs_width(node.left, self.vars)
        if bow >= 256:
            return node

        r_vars = [v for v in get_rhs_vars(node.right)]
        new_reg_var = self.gen_always(get_lhs_width(node.left, self.vars), r_vars, node.left, node.right)
        # node.right = self.make_change(new_reg_var, node.right)
        node.right = new_reg_var
        return node

    def visit_Always(self, node: vast.Always):
        if node.sens_list.list[0].type == 'posedge' or node.sens_list.list[0].type == 'negedge':
            self._sync_proc = True
        for i in range(len(node.sens_list.list)):
            if node.sens_list.list[i].sig is not None:
                self.sense_list.append(node.sens_list.list[i].sig.name)
        node.statement = self.visit(node.statement)
        self.sense_list = []
        return node
