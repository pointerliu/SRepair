# Copyright 2022 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>
from typing import List, Dict, Set

from rtlrepair.analysis import AnalysisResults, VarInfo
from rtlrepair.snn import SNNTemplate
from rtlrepair.snn_templates.utils import collect_blocks, get_lhs_vars, convert_expr2net, CollectUtils
from rtlrepair.utils import Namespace
import pyverilog.vparser.ast as vast
from rtlrepair.visitor import template_guard

_synth_var_prefix = "__synth_"
_synth_change_prefix = "__synth_change_"


# TODD
# generate synth inplace

def t3_replace_assign(ast: vast.Source, analysis: AnalysisResults, glb_enable=False, bound_arch=[]):
    # df = get_dataflow(ast)
    df = None
    namespace = Namespace(ast)
    cu = collect_blocks(ast)
    assignment, blocking_assignment, nonblocking_assignment, cond_vars = cu.assignment, cu.blocking_assignment, cu.nonblocking_assignment, cu.cond_vars
    ops = list(set(cu.ops))
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
    repl = ReplaceAssign(cu, analysis.vars, analysis.widths, df, assignment, blocking_assignment, nonblocking_assignment,
                         ops, bound_arch, glb_enable)
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


class ReplaceAssign(SNNTemplate):
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
            bound_arch: List = [],
            template_global_enable: bool = False
    ):
        super().__init__(cu, vars, widths, dataflow, ast_assignment, blocking_assigment, nonblocking_assigment, ops, bound_arch)
        self.template_global_enable = template_global_enable

    @template_guard
    def visit_Assign(self, node: vast.Assign):
        # if not (
        #         isinstance(node.left.var, vast.Pointer) and
        #         isinstance(node.left.var.var, vast.Pointer) and
        #         isinstance(node.left.var.var.ptr, vast.Identifier) and
        #         node.left.var.var.var.name == 'f'
        # ):
        #     return node

        self.set_bv(self.get_width(node))

        in_vars = self.infer_vars(get_lhs_vars(node.left.var))

        idents, rhs_tree = self.get_rhs_tree(node.right.var)
        expr_net_mapping = convert_expr2net(node.right.var, len(rhs_tree))
        nodes_num = self.infer_arch(expr_net_mapping)

        candi_vars = self.get_candidate_vars(idents, in_vars, expr_net_mapping)

        # if len(idents) != 0:
        self.snn_id = self._bv
        # if self.snn_id not in self.snn_index:
        # snn_expr = self.build_snn(nodes_num=nodes_num[::-1], in_vars=list(set(idents + in_vars)))
        # comb top loop here.

        """
        611s -> 4, 3, 2, 1
        91s -> 3, 2, 1
        """

        # if nodes_num[0] > 3:
        # nodes_num = [3, 2, 1]
        snn_expr = self.build_snn(nodes_num=nodes_num, in_vars=candi_vars,
                                  expr_net_mapping=expr_net_mapping)
        node.right = self.make_change(snn_expr, node.right)
        # else:
        #     snn_expr = self.build_snn(nodes_num=nodes_num, in_vars=candi_vars,
        #                               expr_net_mapping=expr_net_mapping)
        #     if self.template_global_enable:
        #         node.right = self.make_change(snn_expr, node.right)
        #     else:
        #         node.right = snn_expr

        self._gen_place_freeze = True
        return node

    def visit_ForStatement(self, node: vast.ForStatement):
        if not isinstance(node.statement, vast.Block):
            node.statement = vast.Block(statements=[node.statement])
        if not self._gen_place_freeze:
            self._gen_var_place = node.statement
        self.generic_visit(node.statement)
        return node
