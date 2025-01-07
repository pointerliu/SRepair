# Copyright 2022 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>
import difflib
import math
from copy import deepcopy
from heapq import nlargest
from typing import List, Dict, Set

from pyverilog.utils.identifierreplace import children_items
from rtlrepair.repair import RepairTemplate
from rtlrepair.analysis import AnalysisResults, VarInfo
from rtlrepair.snn_templates.utils import get_dataflow, analysis_if_body, collect_blocks, insert_anchor, get_lhs_width, \
    get_lhs_vars, get_rhs_width, convert_expr2net, CollectUtils
from rtlrepair.utils import Namespace
import pyverilog.vparser.ast as vast
from rtlrepair.visitor import template_guard

_synth_var_prefix = "__synth_"
_synth_change_prefix = "__synth_change_"


def _make_wire(name: str, width: int) -> vast.Decl:
    assert width >= 1
    width_node = None if width == 1 else vast.Width(vast.IntConst(str(width - 1)), vast.IntConst("0"))
    return vast.Decl((
        vast.Wire(name, width=width_node),
    ))


def _analysis_rhs(node: vast.Node, depth: int, layers: Dict[int, List[vast.Node]], idents: List[vast.Node]):
    if isinstance(node, vast.IntConst):
        return
    if isinstance(node, vast.Identifier) or isinstance(node, vast.Partselect) or isinstance(node, vast.Pointer) \
            or isinstance(node, vast.Repeat):
        idents.append(node)
        if depth not in layers:
            layers[depth] = []
        layers[depth].append(node)
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
    elif op is vast.Xor:
        return vast.Xor(x0, x1)
    elif op == 'identity':
        return x0
    else:
        return op(x0, x1)
        # raise NotImplementedError(f'Unsupported operator {op} executing')


def check_in_bound(i, j, expr_net_mapping):
    return i < len(expr_net_mapping) and j < len(expr_net_mapping[i])


class SNNTemplate(RepairTemplate):
    def __init__(
            self,
            cu: CollectUtils,
            vars: dict[str, VarInfo],
            widths: dict[vast.Node, int],
            dataflow: Dict[str, Set[str]] = None,
            ast_assignment: List = [],
            blocking_assigment: List = [],
            nonblocking_assigment: List = [],
            ops: List = [],
            bound_arch: List = []
    ):
        super().__init__(name="replace_assign")
        self.cu = cu
        if len(bound_arch) != 0:
            self.bound_arch = bound_arch
        else:
            self.bound_arch = None
        self.dataflow = dataflow
        self.df_next = {}

        self.ast_assignment = ast_assignment
        self.blocking_assigment = blocking_assigment
        self.nonblocking_assigment = nonblocking_assigment

        # for k in self.dataflow:
        #     for v in self.dataflow[k]:
        #         if v not in self.df_next:
        #             self.df_next[v] = set()
        #         self.df_next[v].add(k)

        self.vars = vars
        self.widths = widths
        self.in_proc = False

        self.namespace_id = 0

        self.default_ops = [
            vast.Plus,
            # vast.Minus,
            vast.Unot,
            vast.Or,
            vast.And,
            vast.Xor,
            # vast.Sll,
            # vast.Srl,
            # vast.IntConst,
            # 'identity'
        ]

        self.default_ops = list(set(self.default_ops + ops))
        self.default_ops.append('identity')

        self._sync_proc = False

        self._cond_ops = False
        self.default_cond_ops = [
            vast.Land,
            vast.Lor,
            vast.Eq,
            vast.NotEq,
            vast.Ulnot,
            # vast.LessEq,
            'identity'
        ]

        self.ops_map = {
        }

        self.decl_wires = []
        self.assignments = []

        self.snn_id = 0
        self.snn_index = {}

        self._gen_var_place: vast.Block = None
        self._gen_place_freeze = False

    @staticmethod
    def find_atoms(lvars: List, vars):
        lvars = set(lvars)
        atoms = []
        l_deps = set() if len(lvars) == 0 else set.union(*[vars[v].depends_on for v in lvars])
        for var in vars.values():
            if var.is_clock:
                continue

            # check which only mater for comb assignments
            if len(lvars) > 0 and len(var.depends_on) > 0:
                # check to see if the variable would create a loop
                lvar_deps = lvars & var.depends_on
                if len(lvar_deps) > 0 or var.name in lvars:
                    continue
                # check to see if we would create a new dependency
                new_deps = (var.depends_on | {var.name}) - l_deps
                if len(new_deps) > 0:
                    continue
            # otherwise this might be a good candidate
            atoms.append(var.name)
        return atoms

    def _declare_synth_assign(self):
        res = []
        for lhs, rhs in self.assignments:
            res.append(vast.Assign(lhs, rhs))
        return res

    def _declare_synth_wires(self):
        return [_make_wire(name, width) for name, width in self.decl_wires]

    def add_label_ignore_ex(self, node: vast.Node):
        setattr(node, '_ignore_ex', True)

    def check_label_ignore_ex(self, node: vast.Node):
        try:
            res = getattr(node, '_ignore_ex')
        except AttributeError:
            return False
        return res

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
        wire_decls = self._declare_synth_wires()
        decls = self._declare_synth_regs()

        if self._gen_var_place is None:
            mod_def: vast.ModuleDef = ast.description.definitions[0]
            mod_def.items = tuple(assign_decls + list(mod_def.items))

            mod_def: vast.ModuleDef = ast.description.definitions[0]
            mod_def.items = tuple(wire_decls + list(mod_def.items))

            # declare synthesis vars
            mod_def: vast.ModuleDef = ast.description.definitions[0]
            mod_def.items = tuple(decls + list(mod_def.items))
        else:
            self._gen_var_place.statements = tuple(assign_decls + list(self._gen_var_place.statements))
            self._gen_var_place.statements = tuple(wire_decls + list(self._gen_var_place.statements))

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

    def _gen_guard_link(self, prefix: str, in_vars: List[vast.Node], x: vast.Node, fix_id: int):
        e_guards = []
        for i in range(len(in_vars) - 1):
            e_guard = self._gen_guard_decl(prefix + f'_{i}_e')
            e_guards.append(e_guard)

        # edge_select_width = int(math.ceil(math.log2(len(in_vars) + 1)))
        # edge_selector = vast.Identifier(self.make_synth_var(edge_select_width))
        # # for i in range(len(in_vars) - 1):
        # for i in range(len(in_vars) - 1, 0, -1):
        #     # e_guard = self._gen_guard_decl(prefix + f'_{i}_e')
        #     e_guard = vast.IntConst(f"{edge_select_width}'b{i:b}")
        #     e_guards.append(vast.Eq(edge_selector, e_guard))

        tmp_v = deepcopy(in_vars)
        if fix_id != -1 and fix_id < len(tmp_v):
            v = tmp_v[fix_id]
            tmp_v.remove(v)
            tmp_v.append(v)

            # fix default SRN
            self.assignments.append((x, self._gen_guard_body(e_guards, tmp_v, 0)))
        else:
            self.assignments.append((x, self._gen_guard_body(e_guards, tmp_v[::-1], 0)))

    def _gen_guard_op(self, prefix: str, x0: vast.Identifier, x1: vast.Identifier, ops: List[vast.Node],
                      y: vast.Identifier, fix_id):
        if len(ops) == 0:
            op_body = []
            op_body.append(_op_execute('identity', x0, x1))
            self.assignments.append((y, self._gen_guard_body(op_body, op_body, 0)))
        else:

            op_guards = []
            for i in range(len(ops) - 1):
                op_guard = self._gen_guard_decl(prefix + f'_{i}_op')
                op_guards.append(op_guard)

            # op_select_width = int(math.ceil(math.log2(len(ops))))
            # op_selector = vast.Identifier(self.make_synth_var(op_select_width))
            # for i in range(len(ops) - 1, 0, -1):
            #     # op_guard = self._gen_guard_decl(prefix + f'_{i}_op')
            #     op_guard = vast.IntConst(f"{op_select_width}'b{i:b}")
            #     op_guards.append(vast.Eq(op_selector, op_guard))

            # y = self._gen_wire_decl(prefix, x0.)

            op_body = []
            for op in ops:
                if fix_id is not None and (type(fix_id) == op or fix_id == op):
                    continue
                op_body.append(_op_execute(
                    op,
                    # x0 if op is not vast.IntConst else vast.Identifier(self.make_synth_var(self._bv)),
                    # self.make_change(vast.Identifier(self.make_synth_var(self._bv)), x0),
                    x0,
                    x1)
                )
            if fix_id is not None and type(fix_id) in ops:
                op_body.append(_op_execute(type(fix_id), x0, x1))
            elif fix_id is not None and fix_id in ops:
                op_body.append(_op_execute(fix_id, x0, x1))

            self.assignments.append((y, self._gen_guard_body(op_guards, op_body, 0)))
        return y

    def _build_node(self, prefix: str, l: int, i: int, in_vars: List[vast.Identifier], fix_info):
        if len(in_vars) == 0:
            ops = []
            prefix = f'{prefix}_l_{l}_i_{i}'
            y = self._gen_wire_decl(prefix + '_y', self._bv)
            self._gen_guard_op(
                prefix,
                vast.Identifier(self.make_synth_var(self._bv)),
                None,
                ops,
                y,
                fix_id=None
            )
        else:
            # link
            prefix = f'{prefix}_l_{l}_i_{i}'
            # bv = self.vars[in_vars[0].name]
            x0 = self._gen_wire_decl(prefix + '_x0', self._bv)
            x1 = self._gen_wire_decl(prefix + '_x1', self._bv)

            self._gen_guard_link(prefix=prefix + '_x0', in_vars=in_vars, x=x0,
                                 fix_id=fix_info[1] if fix_info is not None and len(fix_info) >= 2 else -1)
            self._gen_guard_link(prefix=prefix + '_x1', in_vars=in_vars, x=x1,
                                 fix_id=fix_info[2] if fix_info is not None and len(fix_info) >= 3 else -1)
            # ops
            ops = self.get_ops_at(l, i)
            y = self._gen_wire_decl(prefix + '_y', self._bv)
            bias = self.make_synth_var(self._bv)
            # x00 = self.make_change(x0, vast.Identifier(bias))
            x00 = self.make_change(vast.Identifier(bias), x0)
            self._gen_guard_op(prefix, x00, x1, ops, y,
                               fix_id=fix_info[0] if fix_info is not None and len(fix_info) >= 1 else None)
        return y

    def _build_layer(self, prefix: str, l: int, n: int, in_vars: List[vast.Identifier], expr_net_mapping):
        out = []
        for i in range(n):
            y = self._build_node(
                prefix, l, i, in_vars,
                fix_info=expr_net_mapping[l + 1][i]
                if expr_net_mapping is not None and check_in_bound(l + 1, i, expr_net_mapping)
                else None
            )
            out.append(y)
        return out

    def _build(self, prefix: str, nodes_num: List[int], in_vars: List[vast.Node], expr_net_mapping):
        for i in range(len(nodes_num)):
            in_vars = self._build_layer(prefix, i, nodes_num[i], in_vars=in_vars, expr_net_mapping=expr_net_mapping)
        return in_vars

    def build_snn(self, nodes_num: List[int], in_vars: List[vast.Node], expr_net_mapping):
        if self.bound_arch is not None:
            nodes_num = self.bound_arch
        res = self._build(prefix=f'expr_{self.namespace_id}', nodes_num=nodes_num, in_vars=in_vars,
                          expr_net_mapping=expr_net_mapping)
        self.namespace_id += 1
        return res[0]

    def get_width(self, node) -> int:
        l_bv = get_lhs_width(node.left, self.vars)
        try:
            r_bv = get_rhs_width(node.right, self.vars)
        except Exception:
            r_bv = 0
        return max(l_bv, r_bv)

    def set_bv(self, bv):
        self._bv = bv

    def infer_vars(self, nodes: List, is_sync: bool = False):
        if is_sync:
            vs = nodes
        else:
            vs = self.find_atoms(nodes, self.vars)
        return [
            vast.Identifier(name) for name in vs
            # TODO: do we need to set width align ?
            # if (self.vars[name].width == self._bv or self.vars[name].width == 1) and
            #    not self.vars[name].is_genvar and
            #    not self.vars[name].is_vector
            if not self.vars[name].is_genvar and not self.vars[name].is_vector
        ]

    def get_rhs_tree(self, node):
        rhs_tree = {}
        idents = []
        _analysis_rhs(node, 0, rhs_tree, idents)
        return idents, rhs_tree

    def infer_arch(self, expr_net_mapping):
        nodes_num = [len(l) for l in expr_net_mapping]
        for i in range(len(nodes_num) - 1):
            nodes_num[i] += 1
        return nodes_num

    def get_candidate_vars(self, idents, in_vars, expr_net_mapping, merge_idents=False):
        def _get_name(_node: vast.Node):
            if isinstance(_node, vast.Identifier):
                return _node.name
            elif isinstance(_node, vast.Partselect):
                return _get_name(_node.var)
            else:
                print(f'get_candidate_vars -> _get_name NIE for {_node}')
            return _node

        if merge_idents:
            candi_vars = list(set(idents + in_vars[:15]))
        else:
            candi_vars = list(set(idents))
        head_nds = []

        for nd in expr_net_mapping[0]:
            head_nds.append(nd[0])
            if nd[0] in candi_vars:
                candi_vars.remove(nd[0])
            else:
                for v in candi_vars:
                    if _get_name(v) == _get_name(nd[0]):
                        candi_vars.remove(v)
                        break

        candi_vars = head_nds + candi_vars
        return candi_vars


def find_top_k_similar_strings(a, B, k):
    similarities = [(b, difflib.SequenceMatcher(None, a, b).ratio()) for b in B]
    top_k = nlargest(k, similarities, key=lambda x: x[1])
    return [x[0] for x in top_k]

def find_top_k_for_list(A, B, k):
    result = []
    for a in A:
        top_k_similar = find_top_k_similar_strings(a, B, k)
        result.extend(top_k_similar)
    return result