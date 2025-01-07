# Copyright 2022 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>
from typing import List, Dict

from pyverilog.utils.identifierreplace import children_items
from rtlrepair.analysis import AnalysisResults, VarInfo
from rtlrepair.snn import SNNTemplate
from rtlrepair.snn_templates.utils import collect_blocks, insert_anchor, convert_expr2net, CollectUtils
from rtlrepair.utils import Namespace
import pyverilog.vparser.ast as vast
from rtlrepair.visitor import template_guard

_synth_var_prefix = "__synth_"
_synth_change_prefix = "__synth_change_"


def t1_replace_atom(ast: vast.Source, analysis: AnalysisResults, glb_enable=False, bound_arch=None):
    namespace = Namespace(ast)
    cu = collect_blocks(ast)
    assignment, blocking_assignment, nonblocking_assignment, cond_vars = cu.assignment, cu.blocking_assignment, cu.nonblocking_assignment, cu.cond_vars
    ast = insert_anchor(
        ast,
        vars=analysis.vars,
        en_always=False,
        en_case=True,
        en_if=False,
        assignment=assignment,
        blocking_assignment=blocking_assignment,
        nonblocking_assignment=nonblocking_assignment
    )
    repl = ReplaceAtom(cu, analysis.vars, analysis.widths, glb_enable)
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


class ReplaceAtom(SNNTemplate):
    def __init__(
            self,
            cu: CollectUtils,
            vars: dict[str, VarInfo],
            widths: dict[vast.Node, int],
            template_global_enable: bool = False
    ):
        super().__init__(cu, vars, widths)
        self.template_global_enable = template_global_enable

    @template_guard
    def visit_Identifier(self, node: vast.Identifier):
        if node.name not in self.vars:
            return node
        var = self.vars[node.name]
        if var.is_const:
            self._bv = var.width
            expr_net_mapping = convert_expr2net(node, 1)
            new_const = self.build_snn(nodes_num=[1], in_vars=[], expr_net_mapping=expr_net_mapping)
            choice = self.make_change(new_const, node)
            return choice
        else:
            return node

    @template_guard
    def visit_IntConst(self, node: vast.IntConst):
        self._bv = self.widths[node]
        expr_net_mapping = convert_expr2net(node, 1)
        new_const = self.build_snn(nodes_num=[1], in_vars=[], expr_net_mapping=expr_net_mapping)
        choice = self.make_change(new_const, node)
        return choice

    def visit_Always(self, node: vast.Always):
        self.in_proc = True
        node = self.generic_visit(node)
        self.in_proc = False
        return node

    def visit_IfStatement(self, node: vast.IfStatement):
        if self.in_proc:
            node.cond = self.visit(node.cond)
        node.true_statement = self.visit(node.true_statement)
        node.false_statement = self.visit(node.false_statement)
        return node