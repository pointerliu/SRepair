# Copyright 2022 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>
from typing import List, Dict

from pyverilog.utils.identifierreplace import children_items
from rtlrepair.repair import RepairTemplate
from rtlrepair.analysis import AnalysisResults, VarInfo
from rtlrepair.snn_templates.utils import analysis_if_body
from rtlrepair.utils import Namespace
import pyverilog.vparser.ast as vast

_synth_var_prefix = "__synth_"
_synth_change_prefix = "__synth_change_"


def replace_cond_expr(ast: vast.Source, analysis: AnalysisResults):
    namespace = Namespace(ast)
    repl = CondExprReplacer(analysis.vars, analysis.widths)
    repl.apply(namespace, ast)


def _make_wire(name: str, width: int) -> vast.Decl:
    assert width >= 1
    width_node = None if width == 1 else vast.Width(vast.IntConst(str(width - 1)), vast.IntConst("0"))
    return vast.Decl((
        vast.Wire(name, width=width_node),
    ))


def _analysis_rhs(node: vast.Node, depth: int, layers: Dict[int, List[vast.Node]], idents: List[vast.Node]):
    if isinstance(node, vast.IntConst):
        return
    if isinstance(node, vast.Identifier):
        idents.append(node)
        return
    if isinstance(node, vast.Partselect):
        idents.append(node)
        return
    if depth not in layers:
        layers[depth] = []
    layers[depth].append(node)
    for name, child in children_items(node):
        if child is None:
            continue
        if isinstance(child, vast.Node):
            _analysis_rhs(child, depth + 1, layers, idents)


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


class CondExprReplacer(RepairTemplate):
    def __init__(self, vars: dict[str, VarInfo], widths: dict[vast.Node, int]):
        super().__init__(name="expr")
        self.vars = vars
        self.widths = widths
        self.in_proc = False

        self.namespace_id = 0

        self.default_ops = [
            vast.Plus,
            vast.Minus,
            vast.Unot,
            vast.Or,
            vast.And,
            'identity'
        ]

        self._cond_ops = False
        self.default_cond_ops = [
            vast.Land,
            vast.Lor,
            vast.Eq,
            vast.NotEq,
            vast.Ulnot,
            vast.LessEq,
            'identity'
        ]

        self.ops_map = {
        }

        self.decl_wires = []
        self.assignments = []

    def _declare_synth_assign(self):
        res = []
        for lhs, rhs in self.assignments:
            res.append(vast.Assign(lhs, rhs))
        return res

    def _declare_synth_wires(self):
        return [_make_wire(name, width) for name, width in self.decl_wires]

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

        wire_decls = self._declare_synth_wires()
        mod_def: vast.ModuleDef = ast.description.definitions[0]
        mod_def.items = tuple(wire_decls + list(mod_def.items))

        # declare synthesis vars
        decls = self._declare_synth_regs()
        mod_def: vast.ModuleDef = ast.description.definitions[0]
        mod_def.items = tuple(decls + list(mod_def.items))

    def get_ops_at(self, l: int, i: int):
        if f'{l}_{i}' not in self.ops_map:
            if self._cond_ops:
                return self.default_cond_ops
            return self.default_ops
        return self.ops_map[f'{l}_{i}']

    def _gen_guard_decl(self, name: str):
        name: str = self._namespace.new_name(_synth_change_prefix + name + '_g')
        self.changed.append(name)
        return vast.Identifier(name)

    def _gen_wire_decl(self, name: str, width: int):
        self.decl_wires.append((name, width))
        return vast.Identifier(name)

    def _gen_guard_body(self, guards: List[vast.Node], inp: List[vast.Node], i: int):
        if i == len(inp) - 1:
            return inp[-1]
        return vast.Cond(guards[i], inp[i], self._gen_guard_body(guards, inp, i + 1))

    def _gen_guard_link(self, prefix: str, in_vars: List[vast.Node], x: vast.Node):
        e_guards = []
        for i in range(len(in_vars) - 1):
            e_guard = self._gen_guard_decl(prefix + f'_{i}_e')
            e_guards.append(e_guard)

        self.assignments.append((x, self._gen_guard_body(e_guards, in_vars, 0)))

    def _gen_guard_op(self, prefix: str, x0: vast.Identifier, x1: vast.Identifier, ops: List[vast.Node],
                      y: vast.Identifier):
        if len(ops) == 0:
            op_body = []
            op_body.append(_op_execute('identity', x0, x1))
            self.assignments.append((y, self._gen_guard_body(op_body, op_body, 0)))
        else:

            op_guards = []
            for i in range(len(ops) - 1):
                op_guard = self._gen_guard_decl(prefix + f'_{i}_op')
                op_guards.append(op_guard)

            # y = self._gen_wire_decl(prefix, x0.)

            op_body = []
            for op in ops:
                op_body.append(_op_execute(
                    op,
                    # x0 if op is not vast.IntConst else vast.Identifier(self.make_synth_var(self._bv)),
                    self.make_change(vast.Identifier(self.make_synth_var(self._bv)), x0),
                    x1)
                )

            self.assignments.append((y, self._gen_guard_body(op_guards, op_body, 0)))
        return y

    def _build_node(self, prefix: str, l: int, i: int, in_vars: List[vast.Identifier]):
        if len(in_vars) == 0:
            ops = []
            y = self._gen_wire_decl(prefix + '_y', self._bv)
            self._gen_guard_op(
                prefix,
                vast.Identifier(self.make_synth_var(self._bv)),
                None,
                ops,
                y
            )
        else:
            # link
            prefix = f'{prefix}_l_{l}_i_{i}'
            # bv = self.vars[in_vars[0].name]
            x0 = self._gen_wire_decl(prefix + '_x0', self._bv_low if l == 0 else self._bv)
            x1 = self._gen_wire_decl(prefix + '_x1', self._bv_low if l == 0 else self._bv)

            self._gen_guard_link(prefix=prefix + '_x0', in_vars=in_vars, x=x0)
            self._gen_guard_link(prefix=prefix + '_x1', in_vars=in_vars, x=x1)
            # ops
            ops = self.get_ops_at(l, i)
            y = self._gen_wire_decl(prefix + '_y', self._bv)
            self._gen_guard_op(prefix, x0, x1, ops, y)
        return y

    def _build_layer(self, prefix: str, l: int, n: int, in_vars: List[vast.Identifier]):
        out = []
        for i in range(n):
            y = self._build_node(prefix, l, i, in_vars)
            out.append(y)
        return out

    def _build(self, prefix: str, nodes_num: List[int], in_vars: List[vast.Node]):
        for i in range(len(nodes_num)):
            in_vars = self._build_layer(prefix, i, nodes_num[i], in_vars=in_vars)
        return in_vars

    def build_snn(self, nodes_num: List[int], in_vars: List[vast.Node]):
        res = self._build(prefix=f'expr_{self.namespace_id}', nodes_num=nodes_num, in_vars=in_vars)
        self.namespace_id += 1
        return res[0]

    def visit_IfStatement(self, node: vast.IfStatement):
        lhs_if_body = set()
        analysis_if_body(node, lhs_if_body)
        in_vars = [vast.Identifier(name) for name in self.vars if
                   name not in lhs_if_body and self.vars[name].width == 1]

        rhs_tree = {}
        idents = []
        _analysis_rhs(node.cond, 0, rhs_tree, idents)
        nodes_num = [len(rhs_tree[l]) for l in rhs_tree]
        for i in range(1, len(nodes_num)):
            nodes_num[i] += nodes_num[i - 1]
        nodes_num = [1] + nodes_num

        const_bv = 1
        for i in idents:
            if isinstance(i, vast.Partselect):
                const_bv = max(const_bv, int(i.msb.value) - int(i.lsb.value) + 1)
            elif i.name in self.vars:
                const_bv = max(const_bv, self.vars[i.name].width)

        self._bv = const_bv
        self._bv_low = const_bv
        const_expr = self.build_snn(nodes_num=[1], in_vars=list(set(in_vars + idents)))

        self._cond_ops = True
        self._bv = 1
        self._bv_low = const_bv
        node.cond = self.make_change(self.build_snn(nodes_num=nodes_num, in_vars=list(set(in_vars + idents + [const_expr]))), node.cond)
        self._cond_ops = False

        node.true_statement = self.visit(node.true_statement)
        node.false_statement = self.visit(node.false_statement)
        return node

    def visit_CaseStatement(self, node: vast.CaseStatement):
        lhs_if_body = set()
        analysis_if_body(node, lhs_if_body)
        in_vars = [vast.Identifier(name) for name in self.vars if
                   name not in lhs_if_body and self.vars[name].width == 1]

        self._bv = self.vars[node.comp.name].width
        self._bv_low = self._bv

        for i in range(len(node.caselist)):
            if node.caselist[i].cond is None:
                continue
            node.caselist[i].cond = (
                self.make_change(self.build_snn(nodes_num=[1], in_vars=in_vars),
                                 node.caselist[i].cond[0]),
            )

        return node
