# Copyright 2022 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>
from typing import List, Dict, Set

from pyverilog.utils.identifierreplace import children_items
from rtlrepair.analysis import AnalysisResults, VarInfo
from rtlrepair.snn import SNNTemplate
from rtlrepair.snn_templates.utils import analysis_if_body, collect_blocks, get_lhs_width, \
    convert_expr2net, CollectUtils
from rtlrepair.utils import Namespace
import pyverilog.vparser.ast as vast

_synth_var_prefix = "__synth_"
_synth_change_prefix = "__synth_change_"


def t2_replace_cond(ast: vast.Source, analysis: AnalysisResults, glb_enable=False, bound_arch=[]):
    # df = get_dataflow(ast)
    df = None
    namespace = Namespace(ast)
    cu = collect_blocks(ast)
    assignment, blocking_assignment, nonblocking_assignment, cond_vars = cu.assignment, cu.blocking_assignment, cu.nonblocking_assignment, cu.cond_vars
    # ast = insert_anchor(
    #     ast,
    #     en_always=True,
    #     en_case=True,
    #     en_if=True,
    #     assignment=assignment,
    #     blocking_assignment=blocking_assignment,
    #     nonblocking_assignment=nonblocking_assignment
    # )
    # ast = insert_anchor(ast, en_always=False, en_case=False, en_if=True)
    repl = ReplaceCond(
        cu,
        analysis.vars, analysis.widths, df,
        assignment, blocking_assignment, nonblocking_assignment,
        template_global_enable=glb_enable,
        bound_arch=bound_arch
    )
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


class ReplaceCond(SNNTemplate):
    def __init__(
            self,
            cu: CollectUtils,
            vars: dict[str, VarInfo],
            widths: dict[vast.Node, int],
            dataflow: Dict[str, Set[str]],
            ast_assignment: List,
            blocking_assigment: List,
            nonblocking_assigment: List,
            template_global_enable: bool = False,
            bound_arch: List = []
    ):
        super().__init__(cu, vars, widths, dataflow, ast_assignment, blocking_assigment, nonblocking_assigment, bound_arch=bound_arch)
        self.template_global_enable = template_global_enable

    # @template_guard
    def visit_IfStatement(self, node: vast.IfStatement):
        if getattr(node.cond, 'mark', None) is None and not self.template_global_enable:
            return node
        if self.in_proc:
            if self.snn_id in self.snn_index:
                node.cond = self.make_change(
                    self.snn_index[self.snn_id],
                    node.cond
                )
            else:
                lhs_if_body = set()
                analysis_if_body(node, lhs_if_body)
                in_vars = self.infer_vars([v for v in self.vars], is_sync=self._sync_proc)

                self._bv = 1

                idents, rhs_tree = self.get_rhs_tree(node.cond)

                if not (isinstance(node.cond, vast.Identifier) and node.cond.name.startswith(_synth_var_prefix)):
                    const_bv = 1
                    for i in idents:
                        const_bv = max(const_bv, get_lhs_width(i, self.vars))
                    self._bv = const_bv
                    self._bv_low = const_bv
                    # const_expr = self.build_snn(nodes_num=[1], in_vars=list(set(in_vars + idents)))

                    self._cond_ops = True
                    self._bv = 1
                    self._bv_low = const_bv

                    # snn_expr = self.build_snn(nodes_num=nodes_num[::-1], in_vars=list(set(in_vars + idents + [const_expr])))
                    expr_net_mapping = convert_expr2net(node.cond, len(rhs_tree) + 1) # deepen
                    nodes_num = self.infer_arch(expr_net_mapping) # widen
                    candi_vars = self.get_candidate_vars(idents, in_vars, expr_net_mapping, merge_idents=self._sync_proc)

                    snn_expr = self.build_snn(nodes_num=nodes_num, in_vars=candi_vars,
                                              expr_net_mapping=expr_net_mapping)
                    node.cond = self.make_change(
                        snn_expr,
                        node.cond
                    )
                    self._cond_ops = False

                    self.snn_index[self.snn_id] = snn_expr

        node.true_statement = self.visit(node.true_statement)
        node.false_statement = self.visit(node.false_statement)

        return node

    def visit_Always(self, node: vast.Always):
        self.in_proc = True
        self.snn_id += 1
        if node.sens_list.list[0].type == 'posedge' or node.sens_list.list[0].type == 'negedge':
            self._sync_proc = True
        node.statement = self.visit(node.statement)
        self._sync_proc = False
        self.in_proc = False
        return node
