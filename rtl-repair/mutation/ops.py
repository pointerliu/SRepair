import random
import shutil
from copy import deepcopy
from pathlib import Path

import pyverilog.vparser.ast as vast
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
from pyverilog.vparser.parser import VerilogCodeParser

from mutation.base import MutationOp, serialize
from rtlrepair.analysis import analyze_ast
from rtlrepair.snn_templates.utils import get_rhs_width, get_lhs_width


class ASTCollector:
    def __init__(self):
        self.u_ops = set()
        self.ops = set()
        self.const = set()

        self.mod_pos = []
        self.f_subs = False

    @staticmethod
    def at_subs(f):
        def wrapper(self, ast):
            if ast.__class__.__name__ in ['BlockingSubstitution', 'Assign', 'NonblockingSubstitution']:
                self.f_subs = True
                f(self, ast)
                self.f_subs = False
            else:
                f(self, ast)

        return wrapper

    @at_subs
    def collect(self, ast):
        if ast.__class__.__name__ in ['BlockingSubstitution', 'Assign', 'NonblockingSubstitution']:
            if isinstance(ast.right.var, vast.IntConst):
                return
            self.mod_pos.append(ast)

        for child in ast.children():
            if child is not None:

                if self.f_subs:
                    if isinstance(child, vast.UnaryOperator):
                        self.u_ops.add(child.__class__)
                    elif isinstance(child, vast.Operator):
                        if isinstance(child, vast.Cond) or isinstance(child, vast.Divide):
                            pass
                        else:
                            self.ops.add(child.__class__)

                if isinstance(child, vast.Constant):
                    self.const.add(child)
                self.collect(child)


def get_width(node, vars):
    if (isinstance(node, vast.BlockingSubstitution) or
            isinstance(node, vast.Assign) or
            isinstance(node, vast.NonblockingSubstitution)):
        return get_lhs_width(node.left, vars)
    else:
        return get_rhs_width(node, vars)


class MutateExpr:
    def __init__(self, ast):
        super().__init__()
        analysis_res = analyze_ast(ast)
        self.vars = analysis_res.vars

        self.ast = ast
        self.used_ops = []

    def random_new_ops(self, node: vast.Node, cu):
        if isinstance(node, vast.UnaryOperator):
            op = random.choice(list(set(list(cu.u_ops) + [vast.Unot])))
            self.used_ops.append(op.__name__)
            return op(right=node.right)
        elif isinstance(node, vast.Operator):
            op = random.choice(list(set(list(cu.ops) + [vast.And])))
            self.used_ops.append(op.__name__)
            return op(left=node.left, right=node.right)

    def replace_recur(self, node: vast.Node, cu, mut_cnt: int):
        if mut_cnt == 0:
            return mut_cnt
        if isinstance(node, vast.Pointer):
            return mut_cnt
        if isinstance(node, vast.IndexedPartselect):
            return mut_cnt
        if isinstance(node, vast.Partselect):
            return mut_cnt
        if isinstance(node, vast.Cond):
            mut_cnt = self.replace_recur(node.cond, cu, mut_cnt)
            mut_cnt = self.replace_recur(node.true_value, cu, mut_cnt)
            mut_cnt = self.replace_recur(node.false_value, cu, mut_cnt)
            return mut_cnt
        if isinstance(node, vast.IntConst) and random.random() > 0.5:
            const = random.choice(list(cu.const))
            self.used_ops.append(const.value)
            MutationOp.replace_with_node(self.ast, node, const)
            return mut_cnt - 1

        if isinstance(node, vast.Operator) and random.random() > 0.5:
            new_node = self.random_new_ops(node, cu)
            MutationOp.replace_with_node(self.ast, node, new_node)
            mut_cnt -= 1

        if isinstance(node, vast.Identifier) and random.random() > 0.5:
            if random.random() > 0.5:
                new_node = self.random_new_ops(vast.Plus(left=node, right=node), cu)
            else:
                new_node = self.random_new_ops(vast.Unot(right=node), cu)
            MutationOp.replace_with_node(self.ast, node, new_node)
            return mut_cnt - 1

            # if isinstance(node, vast.Identifier):
            #     try:
            #         op = random.choice(list(cu.ops))
            #     except IndexError:
            #         return
            #     self.used_ops.append(op.__name__)
            #     new_node = op(right=node, left=node)
            #     MutationOp.replace_with_node(self.ast, node, new_node)
        for child in node.children():
            if isinstance(child, vast.Lvalue):
                continue
            mut_cnt = self.replace_recur(child, cu, mut_cnt)
        return mut_cnt

    def apply(self, ast, mod_node, cu, mut_single_var: str, mut_cnt: int = 5):
        if ast is mod_node:
            # if (mut_single_var == 'single' and get_width(mod_node, self.vars) == 1) or (
            #         mut_single_var == 'multi' and get_width(mod_node, self.vars) > 1) or (mut_single_var == 'both'):
            r = self.replace_recur(ast, cu, mut_cnt)
            return ast, r < mut_cnt
        f = False
        for child in ast.children():
            if child is not None:
                _, r = self.apply(child, mod_node, cu, mut_single_var)
                f = f | r
        return ast, f


def do_expr_mutation(ast, max_cnt, visited_pos, mut_var_width):
    cpy_ast = deepcopy(ast)
    cu = ASTCollector()
    cu.collect(cpy_ast)

    mod_pos_filtering = []
    _vars = analyze_ast(ast).vars
    for mp in cu.mod_pos:
        if mut_var_width == 'both':
            mod_pos_filtering.append(mp)
        elif mut_var_width == 'single' and get_width(mp, _vars) == 1:
            mod_pos_filtering.append(mp)
        elif mut_var_width == 'multi' and get_width(mp, _vars) > 1:
            mod_pos_filtering.append(mp)

    if len(mod_pos_filtering) == 0:
        return False, cpy_ast

    max_cnt = min(len(mod_pos_filtering), max_cnt)
    pos = random.sample(mod_pos_filtering, max_cnt)

    f_succ = True
    for p_node in pos:
        mt = MutateExpr(cpy_ast)
        p_node_cpy = deepcopy(p_node)
        cpy_ast, mod_succ = mt.apply(cpy_ast, p_node, cu, mut_var_width)
        if mod_succ and (p_node_cpy, deepcopy(set(mt.used_ops))) not in visited_pos:
            visited_pos.append((p_node_cpy, deepcopy(set(mt.used_ops))))
        else:
            f_succ = False
            break
    return f_succ, cpy_ast
