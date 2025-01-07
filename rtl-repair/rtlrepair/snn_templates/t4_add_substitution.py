# Copyright 2022 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>
from copy import deepcopy
from typing import List, Dict, Set

from rtlrepair.analysis import AnalysisResults, VarInfo
from rtlrepair.snn import SNNTemplate
from rtlrepair.snn_templates.utils import collect_blocks, insert_anchor, convert_expr2net, CollectUtils
from rtlrepair.utils import Namespace
import pyverilog.vparser.ast as vast
from rtlrepair.visitor import template_guard

_synth_var_prefix = "__synth_"
_synth_change_prefix = "__synth_change_"


def t4_add_substitution(ast: vast.Source, analysis: AnalysisResults, bound_arch=[]):
    # df = get_dataflow(ast)
    df = None
    namespace = Namespace(ast)
    cu = collect_blocks(ast)
    assignment, blocking_assignment, nonblocking_assignment, cond_vars = cu.assignment, cu.blocking_assignment, cu.nonblocking_assignment, cu.cond_vars
    ops = cu.ops
    ast = insert_anchor(
        ast,
        vars=analysis.vars,
        en_always=True,
        en_case=False,
        en_if=False,
        assignment=assignment,
        blocking_assignment=blocking_assignment,
        nonblocking_assignment=nonblocking_assignment
    )
    # ast = insert_anchor(ast, en_always=False, en_case=False, en_if=True)
    repl = AddSubstitution(cu, analysis.vars, analysis.widths, df, assignment, blocking_assignment, nonblocking_assignment,
                           ops, bound_arch)
    repl.apply(namespace, ast)


def _make_wire(name: str, width: int) -> vast.Decl:
    assert width >= 1
    width_node = None if width == 1 else vast.Width(vast.IntConst(str(width - 1)), vast.IntConst("0"))
    return vast.Decl((
        vast.Wire(name, width=width_node),
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
    elif op is vast.Xor:
        return vast.Xor(x0, x1)
    elif op == 'identity':
        return x0
    else:
        return op(x0, x1)
        # raise NotImplementedError(f'Unsupported operator {op} executing')


class AddSubstitution(SNNTemplate):
    def __init__(
            self,
            cu: CollectUtils,
            vars: dict[str, VarInfo],
            widths: dict[vast.Node, int],
            dataflow: Dict[str, Set[str]],
            ast_assignment: List,
            blocking_assigment: List,
            nonblocking_assigment: List,
            ops: List,
            bound_arch: List = []
    ):
        super().__init__(cu, vars, widths, dataflow, ast_assignment, blocking_assigment, nonblocking_assigment, ops, bound_arch)
        self.always_anchor_blk = None

    def insert_init_anchor(self, alw_blk, node):
        if self._sync_proc:
            gen_expr = vast.NonblockingSubstitution(
                left=node.left,
                right=vast.Identifier(self.make_synth_var(self.get_width(node)))
            )
        else:
            gen_expr = vast.BlockingSubstitution(
                left=node.left,
                right=vast.Identifier(self.make_synth_var(self.get_width(node)))
            )

        if alw_blk is not None:
            init_expr = vast.IfStatement(
                cond=vast.Identifier(self.make_synth_var(1)),
                true_statement=vast.Block(
                    statements=[
                        gen_expr
                    ]
                ),
                false_statement=None
            )
            alw_blk.statement.statements = tuple([init_expr, *alw_blk.statement.statements])

    @template_guard
    def visit_NonblockingSubstitution(self, node: vast.NonblockingSubstitution):
        if not self._sync_proc:
            gen = vast.BlockingSubstitution(left=deepcopy(node.left), right=deepcopy(node.right))
            gen = self.visit(gen)
            node.left = gen.left
            node.right = gen.right
            return node


        self.set_bv(self.get_width(node))

        in_vars = self.infer_vars([v for v in self.vars], is_sync=True)
        # self._bv = get_lhs_width(node.left, self.vars)

        idents, rhs_tree = self.get_rhs_tree(node.right.var)
        expr_net_mapping = convert_expr2net(node.right.var, len(rhs_tree))
        nodes_num = self.infer_arch(expr_net_mapping)

        candi_vars = self.get_candidate_vars(idents, in_vars, expr_net_mapping, merge_idents=True)

        # if self.snn_id in self.snn_index:
        #     snn_expr = self.snn_index[self.snn_id]
        # else:
        snn_expr = self.build_snn(nodes_num=nodes_num, in_vars=candi_vars,
                                  expr_net_mapping=expr_net_mapping)
        # if you do not use change, the generated NSR may be just correct without modification -> NoRepair
        node.right = self.make_change(snn_expr, node.right)
        # else:
        #     node.right = self.build_snn(nodes_num=[1], in_vars=[])
        self.always_anchor_blk = node
        return node

    @template_guard
    def visit_BlockingSubstitution(self, node: vast.BlockingSubstitution):
        if self._sync_proc:
            gen = vast.NonblockingSubstitution(left=deepcopy(node.left), right=deepcopy(node.right))
            gen = self.visit(gen)
            node.left = gen.left
            node.right = gen.right
            return node

        # if not (isinstance(node.left.var, vast.Identifier) and node.left.var.name == "rd_ptr_next"):
        #     return node
        # debug
        # return node

        # ignore pointer
        # if isinstance(node.left.var, vast.Pointer):
        #     return node

        self.set_bv(self.get_width(node))
        in_vars = self.infer_vars([v for v in self.vars])

        idents, rhs_tree = self.get_rhs_tree(node.right.var)
        expr_net_mapping = convert_expr2net(node.right.var, len(rhs_tree))
        nodes_num = self.infer_arch(expr_net_mapping)

        candi_vars = self.get_candidate_vars(idents, in_vars, expr_net_mapping)
        # if len(idents) != 0:
        # if self.snn_id in self.snn_index:
        #     snn_expr = self.snn_index[self.snn_id]
        # else:
        snn_expr = self.build_snn(nodes_num=nodes_num, in_vars=candi_vars,
                                  expr_net_mapping=expr_net_mapping)
        node.right = self.make_change(snn_expr, node.right)
        # else:
        #     node.right = self.build_snn(nodes_num=[1], in_vars=[])
        self.always_anchor_blk = node
        return node

    def visit_Always(self, node: vast.Always):
        if not isinstance(node.statement, vast.Block):
            node.statement = vast.Block(statements=[node.statement])
        self.always_anchor_blk = None
        self.snn_id += 1
        if node.sens_list.list[0].type == 'posedge' or node.sens_list.list[0].type == 'negedge':
            self._sync_proc = True
        node.statement = self.visit(node.statement)
        if self.always_anchor_blk is not None:
            self.insert_init_anchor(node, self.always_anchor_blk)
        self._sync_proc = False
        # self.always_anchor_blk = None
        return node
