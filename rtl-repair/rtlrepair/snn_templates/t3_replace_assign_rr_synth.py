# Copyright 2022 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>
from typing import List, Dict, Set

from rtlrepair.analysis import AnalysisResults, VarInfo, get_lvars
from rtlrepair.snn import SNNTemplate
from rtlrepair.snn_templates.utils import collect_blocks, get_lhs_vars, convert_expr2net, CollectUtils
from rtlrepair.utils import Namespace
import pyverilog.vparser.ast as vast
from rtlrepair.visitor import template_guard

_synth_var_prefix = "__synth_"
_synth_change_prefix = "__synth_change_"


# TODD
# generate synth inplace


def fals(bv: int = 1):
    return vast.IntConst(f"{bv}'d0")


def tru(bv: int = 1):
    return vast.Unot(fals(bv))


def t3_replace_assign_rr_synth(ast: vast.Source, analysis: AnalysisResults, glb_enable=False, bound_arch=[]):
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
    repl = ReplaceAssign(cu, analysis.vars, analysis.widths, df, assignment, blocking_assignment,
                         nonblocking_assignment,
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
        super().__init__(cu, vars, widths, dataflow, ast_assignment, blocking_assigment, nonblocking_assigment, ops,
                         bound_arch)
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

        # the template from RR can't process multi-bit variables.
        # so we constrain our assign template.

        # atoms = find_atoms(get_lvars(node.left), self.vars)
        in_vars = self.infer_vars(get_lhs_vars(node.left.var))
        idents, rhs_tree = self.get_rhs_tree(node.right.var)
        expr_net_mapping = convert_expr2net(node.right.var, len(rhs_tree))
        atoms = self.get_candidate_vars(idents, in_vars, expr_net_mapping)

        node.right.var = self.build_guard(node.right.var, atoms, bv=self.get_width(node))
        self._gen_place_freeze = True
        return node

    def visit_ForStatement(self, node: vast.ForStatement):
        if not isinstance(node.statement, vast.Block):
            node.statement = vast.Block(statements=[node.statement])
        if not self._gen_place_freeze:
            self._gen_var_place = node.statement
        self.generic_visit(node.statement)
        return node

    def build_guard(self, expr: vast.Node, atoms: list[vast.Node], bv: int) -> vast.Node:
        """
        Our template is essentially: (!?)(...) && ((!)?a || (!?)b)
        Cost is:
            - 1 for inverting the original condition
            - 1 for adding guard a
            - 1 for adding guard b
        """
        may_invert = self.make_inversion(expr, width=bv, free=True)
        if len(atoms) == 0:
            return may_invert
        a = self.build_guard_item(atoms, width=bv)
        b = self.build_guard_item(atoms, width=bv)
        may_b = self.make_change(b, fals(bv))  # false is the neutral element
        a_or_b = vast.Or(a, may_b)
        may_a_or_b = self.make_change(a_or_b, tru(bv))  # true is the neutral element
        return vast.And(may_invert, may_a_or_b)

    def build_guard_item(self, atoms: list[vast.Node], width: int = 1) -> vast.Node:
        out = self.make_choice(atoms)
        # may invert for free
        return self.make_inversion(out, free=True, width=width)


def find_atoms(lvars: set[str], vars) -> list[vast.Node]:
    verbose = False
    atoms = []
    l_deps = set() if len(lvars) == 0 else set.union(*[vars[v].depends_on for v in lvars])
    if verbose:
        print(f"l_deps={l_deps}")
    for var in vars.values():
        # we are only interested in 1-bit vars
        # if var.width != 1:
        #     continue
        # ignore clock signals
        if var.is_clock:
            continue

        # check which only mater for comb assignments
        if len(lvars) > 0 and len(var.depends_on) > 0:
            # check to see if the variable would create a loop
            lvar_deps = lvars & var.depends_on
            if len(lvar_deps) > 0 or var.name in lvars:
                continue
            # check to see if we would create a new dependency
            if verbose:
                print(f"{var.name}.depends_on = {var.depends_on}")
            new_deps = (var.depends_on | {var.name}) - l_deps
            if len(new_deps) > 0:
                continue
        # otherwise this might be a good candidate
        atoms.append(vast.Identifier(var.name))
    return atoms
