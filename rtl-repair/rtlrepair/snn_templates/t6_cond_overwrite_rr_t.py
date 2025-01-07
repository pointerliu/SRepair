# Copyright 2022 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>
from typing import List, Dict, Set

from rtlrepair.analysis import AnalysisResults, VarInfo, get_lvars, get_rvars
from rtlrepair.snn import SNNTemplate
from rtlrepair.snn_templates.utils import collect_blocks, get_lhs_vars, convert_expr2net, CollectUtils
from rtlrepair.templates.assign_const import ProcessAnalyzer
from rtlrepair.utils import Namespace, ensure_block
import pyverilog.vparser.ast as vast
from rtlrepair.visitor import template_guard

_synth_var_prefix = "__synth_"
_synth_change_prefix = "__synth_change_"

# TODD
# generate synth inplace

tru = vast.IntConst("1'b1")
fals = vast.IntConst("1'b0")


def t6_cond_overwrite_rr_t_pre(ast: vast.Source, analysis: AnalysisResults, glb_enable=False, bound_arch=[]):
    # df = get_dataflow(ast)
    df = None
    namespace = Namespace(ast)
    cu = collect_blocks(ast)
    assignment, blocking_assignment, nonblocking_assignment, cond_vars = cu.assignment, cu.blocking_assignment, cu.nonblocking_assignment, cu.cond_vars
    ops = list(set(cu.ops))
    repl = CondOver(cu, analysis.vars, analysis.widths, df, assignment, blocking_assignment,
                    nonblocking_assignment,
                    ops, bound_arch, glb_enable, pre=True)
    repl.apply(namespace, ast)


def t6_cond_overwrite_rr_t_post(ast: vast.Source, analysis: AnalysisResults, glb_enable=False, bound_arch=[]):
    # df = get_dataflow(ast)
    df = None
    namespace = Namespace(ast)
    cu = collect_blocks(ast)
    assignment, blocking_assignment, nonblocking_assignment, cond_vars = cu.assignment, cu.blocking_assignment, cu.nonblocking_assignment, cu.cond_vars
    ops = list(set(cu.ops))
    repl = CondOver(cu, analysis.vars, analysis.widths, df, assignment, blocking_assignment,
                    nonblocking_assignment,
                    ops, bound_arch, glb_enable, pre=False)
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


class CondOver(SNNTemplate):
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
            template_global_enable: bool = False,
            pre: bool = False,
    ):
        super().__init__(cu, vars, widths, dataflow, ast_assignment, blocking_assigment, nonblocking_assigment, ops,
                         bound_arch)
        self.template_global_enable = template_global_enable
        self.blockified = []
        self.pre = pre

    @template_guard
    def visit_Always(self, node: vast.Always):
        analysis = ProcessAnalyzer()
        analysis.run(node)
        if analysis.non_blocking_count > 0 and analysis.blocking_count > 0:
            print("WARN: single always process seems to mix blocking and non-blocking assignment. Skipping.")
            return node
        # collect local condition atoms
        conditions = collect_condition_atoms(analysis.conditions)
        # note: we are ignoring pointer for now since these might contain loop vars that may not always be in scope..
        assigned_vars = [var for var in analysis.assigned_vars if isinstance(var, vast.Identifier)]
        self.use_blocking = analysis.blocking_count > 0
        # add conditional overwrites to the end of the process
        stmts_before, stmts_after = [], []
        if self.pre:
            stmts_before = self.gen_assignments(assigned_vars, conditions, analysis)
        else:
            stmts_after = self.gen_assignments(assigned_vars, conditions, analysis)
        # append statements
        node.statement = ensure_block(node.statement, self.blockified)
        node.statement.statements = tuple(stmts_before + list(node.statement.statements) + stmts_after)
        return node

    def gen_assignments(self, assigned_vars, conditions, analysis):
        stmts = []
        for var in assigned_vars:
            lvars = get_lvars(var)
            filtered_conditions = filter_atom(conditions, lvars, self.vars)
            filtered_case_inputs = filter_atom(analysis.case_inputs, lvars, self.vars)
            if len(filtered_conditions) > 0 or len(filtered_case_inputs) > 0:
                cond = self.gen_condition(filtered_conditions, filtered_case_inputs)
                assignment = self.make_assignment(var)
                inner = vast.IfStatement(cond, assignment, None)
                stmts.append(self.make_change_stmt(inner, 0))
        return stmts

    def make_assignment(self, var):
        width = self.widths[var]
        const = vast.Identifier(self.make_synth_var(width))
        if self.use_blocking:
            assign = vast.BlockingSubstitution(vast.Lvalue(var), vast.Rvalue(const))
        else:
            assign = vast.NonblockingSubstitution(vast.Lvalue(var), vast.Rvalue(const))
        return assign

    def gen_condition(self, conditions: list, case_inputs: list) -> vast.Node:
        atoms = conditions + [vast.Eq(ci, vast.Identifier(self.make_synth_var(self.widths[ci]))) for ci in case_inputs]
        # # atoms can be inverted
        # atoms_or_inv = [self.make_synth_choice(aa, vast.Ulnot(aa)) for aa in atoms]
        # # atoms do not need to be used
        # atoms_optional = [self.make_change(aa, tru) for aa in atoms_or_inv]
        # # combine all atoms together
        # node = atoms_optional[0]
        # for aa in atoms_optional[1:]:
        #     node = vast.And(node, aa)
        self.set_bv(1)
        node = self.build_snn(
            nodes_num=[3, 2, 1],
            in_vars=atoms,
            expr_net_mapping=None
        )
        return node

    def make_synth_choice(self, a, b):
        name = self.make_synth_var(1)
        return vast.Cond(vast.Identifier(name), a, b)


def filter_atom(atoms: list, lvars: set[str], info: dict[str, VarInfo]) -> list:
    # we can only use something as a condition, if it does not depend on any of the lvalues
    out = []
    for atom in atoms:
        atom_vars = get_rvars(atom)
        if atom_dep_ok(atom_vars, lvars, info):
            out.append(atom)
    return out


def atom_dep_ok(atom_vars: set[str], lvars: set[str], info: dict[str, VarInfo]) -> bool:
    for av in atom_vars:
        ai = info[av]
        if len(lvars & ai.depends_on) > 0:
            return False
    return True


def collect_condition_atoms(conditions: list) -> list:
    atoms = set()
    for cond in conditions:
        atoms |= destruct_to_atom(cond)
    return list(atoms)


def destruct_to_atom(expr: list) -> set:
    """ conjunction and negation is already part of our template, thus we want to exclude it from our atoms """
    if isinstance(expr, vast.Unot) or isinstance(expr, vast.Ulnot):
        return destruct_to_atom(expr.right)
    elif isinstance(expr, vast.Land):
        return destruct_to_atom(expr.left) | destruct_to_atom(expr.right)
    else:
        return {expr}
