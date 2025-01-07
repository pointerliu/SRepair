import math
from copy import deepcopy
from typing import List, Set

import pyverilog.vparser.ast as vast
from pyverilog.dataflow.bindvisitor import BindVisitor
import pyverilog.dataflow.dataflow as vdf
from pyverilog.dataflow.modulevisitor import ModuleVisitor
from pyverilog.dataflow.signalvisitor import SignalVisitor
from rtlrepair.analysis import get_lvars
from rtlrepair.repair import RepairTemplate
from rtlrepair.templates.assign_const import ProcessAnalyzer
from rtlrepair.templates.conditional_overwrite import filter_atom
from rtlrepair.utils import Namespace


def convert_expr2net(node: vast.Node, max_depth: int):
    level_ids = {}

    class OpNode:
        def __init__(self, op):
            self.op = op

    def _proc(cur_node: vast.Node, c_depth: int):
        if c_depth not in level_ids:
            level_ids[c_depth] = 0
        c_net = {}
        if (isinstance(cur_node, vast.Identifier) or
                isinstance(cur_node, vast.Partselect) or
                isinstance(cur_node, vast.Pointer) or
                isinstance(cur_node, vast.Repeat) or
                isinstance(cur_node, vast.IntConst)
        ):
            if c_depth < max_depth:
                c_net['name'] = OpNode(op='identity')
                c_net['child'] = [_proc(cur_node, c_depth + 1)]
                c_net['id'] = level_ids[c_depth]
                level_ids[c_depth] += 1
                return c_net
            else:
                c_net['name'] = OpNode(op=cur_node)
                c_net['child'] = []
                c_net['id'] = level_ids[c_depth]
                level_ids[c_depth] += 1
                return c_net

        if isinstance(cur_node, vast.UnaryOperator):
            c_net['name'] = OpNode(op=cur_node)
            c_net['child'] = [_proc(cur_node.right, c_depth + 1)]
            c_net['id'] = level_ids[c_depth]
            level_ids[c_depth] += 1
        elif isinstance(cur_node, vast.Cond):
            # TODO
            c_net['name'] = OpNode(op=cur_node)
            c_net['child'] = [_proc(cur_node.cond, c_depth + 1),
                              _proc(cur_node.true_value, c_depth + 1),
                              _proc(cur_node.false_value, c_depth + 1), ]
            c_net['id'] = level_ids[c_depth]
            level_ids[c_depth] += 1
        elif isinstance(cur_node, vast.Operator):
            c_net['name'] = OpNode(op=cur_node)
            c_net['child'] = [_proc(cur_node.left, c_depth + 1), _proc(cur_node.right, c_depth + 1)]
            c_net['id'] = level_ids[c_depth]
            level_ids[c_depth] += 1
        elif isinstance(cur_node, vast.Concat):
            c_net['name'] = OpNode(op=cur_node)
            c_net['child'] = []
            for c in cur_node.list:
                c_net['child'].append(_proc(c, c_depth + 1))
            c_net['id'] = level_ids[c_depth]
            level_ids[c_depth] += 1
            # print(cur_node)
        elif isinstance(cur_node, vast.IndexedPartselect):
            # replace with id
            c_net['name'] = OpNode(op='identity')
            c_net['child'] = [_proc(cur_node.var, c_depth + 1)]
            c_net['id'] = level_ids[c_depth]
            level_ids[c_depth] += 1
        else:
            raise NotImplementedError(cur_node)

        return c_net

    expr_net = _proc(node, 1)
    mappings = []
    total_map = {}

    def _traverse(c_node: dict, c_depth):
        total_map[c_node['name']] = c_node['child']
        if c_depth >= len(mappings):
            mappings.append({})

        mappings[c_depth][c_node['name']] = c_node['id']
        for ch in c_node['child']:
            _traverse(ch, c_depth + 1)

    _traverse(expr_net, 0)

    ret = []
    for i in range(len(mappings)):
        ret.append([])
        for nd in mappings[i]:
            temp_tup = [nd.op]
            # ret[i].append([nd.op])
            for ch in total_map[nd]:
                temp_tup.append(mappings[i + 1][ch['name']])
            ret[i].append(tuple(temp_tup))

    return ret[::-1]


def get_lhs_vars(node: vast.Node):
    vars = []
    if isinstance(node, vast.Identifier):
        vars.append(node.name)
    elif isinstance(node, vast.LConcat):
        for v in node.list:
            vars.append(v.name)
    elif isinstance(node.var, vast.Partselect):
        vars.append(node.var.var.name)
    elif isinstance(node.var, vast.Pointer):
        vars.extend(get_lhs_vars(node.var.var))
    elif isinstance(node.var, vast.LConcat):
        for v in node.var.list:
            vars.extend(get_lhs_vars(v))
    return vars


def get_lhs_width(node: vast.Node, vars):
    if isinstance(node, vast.Lvalue):
        return get_lhs_width(node.var, vars)

    bv = 1
    # if isinstance(node, vast.Substitution):
    try:
        if isinstance(node, vast.Partselect):
            bv = int(node.msb.value) - int(node.lsb.value) + 1
        elif isinstance(node, vast.LConcat):
            for v in node.list:
                bv += vars[v.name].width
        elif isinstance(node, vast.Pointer):
            bv = get_lhs_width(node.var, vars)
        elif isinstance(node, vast.IndexedPartselect):
            if isinstance(node.stride, vast.IntConst):
                bv = int(node.stride.value)
            else:
                bv = 2
        else:
            bv = vars[node.name].width
    except Exception as e:
        print(f"#ERROR at get_lhs_width# {e}")
        # return bv

    return bv


def verilog_literal_to_int(verilog_literal):
    width_str, value_str = verilog_literal.split("'")
    width = int(width_str)
    base = value_str[0].lower()
    value = value_str[1:]
    if base == 'b':
        integer_value = int(value, 2)
    elif base == 'o':
        integer_value = int(value, 8)
    elif base == 'd':
        integer_value = int(value, 10)
    elif base == 'h':
        integer_value = int(value, 16)
    else:
        raise ValueError("Unknown base '{}' in Verilog literal.".format(base))

    return integer_value, width

def get_rhs_width(node: vast.Node, vars):
    if isinstance(node, vast.Rvalue):
        return get_rhs_width(node.var, vars)
    if isinstance(node, vast.IntConst):
        return verilog_literal_to_int(node.value)[1]

    bv = 1
    # if isinstance(node, vast.Substitution):
    try:
        if isinstance(node, vast.Partselect):
            bv = int(node.msb.value) - int(node.lsb.value) + 1
        elif isinstance(node, vast.Concat):
            for v in node.list:
                bv += vars[v.name].width
        elif isinstance(node, vast.Pointer):
            bv = get_rhs_width(node.var, vars)
        elif isinstance(node, vast.UnaryOperator):
            bv = get_rhs_width(node.right, vars)
        elif isinstance(node, vast.Operator):
            bv = min(get_rhs_width(node.left, vars), get_rhs_width(node.right, vars))
        else:
            bv = vars[node.name].width
    except Exception as e:
        print(f"#ERROR# {e}")
        # return bv

    return bv


def get_rhs_vars(node: vast.Node):
    if isinstance(node, vast.Rvalue):
        return get_rhs_vars(node.var)
    rets = []
    if isinstance(node, vast.Identifier):
        rets.append(node)
    elif isinstance(node, vast.Concat):
        rets.append(node)
    elif isinstance(node, vast.Partselect):
        rets.append(node)
    elif isinstance(node, vast.Pointer):
        rets.append(node)
    elif isinstance(node, vast.Cond):
        rets.extend(get_rhs_vars(node.cond))
        rets.extend(get_rhs_vars(node.true_value))
        rets.extend(get_rhs_vars(node.false_value))
    elif isinstance(node, vast.UnaryOperator):
        rets.extend(get_rhs_vars(node.right))
    elif isinstance(node, vast.Operator):
        rets.extend(get_rhs_vars(node.left))
        rets.extend(get_rhs_vars(node.right))
    return rets


def analysis_if_body(node: vast.Node, lhs_var: Set[str]):
    if node is None:
        return
    if isinstance(node, vast.BlockingSubstitution) or isinstance(node, vast.NonblockingSubstitution):
        if isinstance(node.left.var, vast.Partselect):
            lhs_var.add(node.left.var.var.name)
        elif isinstance(node.left.var, vast.Pointer):
            lhs_var.add(node.left.var.var.name)
        elif isinstance(node.left.var, vast.LConcat):
            for v in node.left.var.list:
                lhs_var.add(v.name)
        elif isinstance(node.left.var, vast.IndexedPartselect):
            lhs_var.add(node.left.var.var.name)
        else:
            lhs_var.add(node.left.var.name)
        return
    if isinstance(node, vast.Block):
        for stat in node.statements:
            analysis_if_body(stat, lhs_var)
        return
    if isinstance(node, vast.IfStatement):
        analysis_if_body(node.true_statement, lhs_var)
        analysis_if_body(node.false_statement, lhs_var)
        return
    if isinstance(node, vast.CaseStatement):
        for case in node.caselist:
            analysis_if_body(case.statement, lhs_var)
        return


def _collect_dataflow(node: vdf.DFNode, res: Set):
    if isinstance(node, vdf.DFTerminal):
        res.add(node.name[-1].scopename)
        return
    if isinstance(node, vdf.DFBranch):
        _collect_dataflow(node.condnode, res)
        _collect_dataflow(node.falsenode, res)
        _collect_dataflow(node.truenode, res)
    if isinstance(node, vdf.DFOperator):
        for n in node.nextnodes:
            _collect_dataflow(n, res)


def get_dataflow(ast: vast.Source):
    module_visitor = ModuleVisitor()
    module_visitor.visit(ast)
    # modulenames = module_visitor.get_modulenames()
    moduleinfotable = module_visitor.get_moduleinfotable()
    topmodule = list(moduleinfotable.dict)[0]
    signal_visitor = SignalVisitor(moduleinfotable, topmodule)
    signal_visitor.start_visit()
    frametable = signal_visitor.getFrameTable()

    bind_visitor = BindVisitor(moduleinfotable, topmodule, frametable)
    bind_visitor.start_visit()
    dataflow = bind_visitor.getDataflows()

    # frametable = bind_visitor.getFrameTable()
    # terms = dataflow.getTerms()
    binddict = dataflow.getBinddict()

    df = {}
    for bk, bv in sorted(binddict.items(), key=lambda x: str(x[0])):

        for bvi in bv:
            # print(bk, bvi.tostr())
            if bvi.dest[-1].scopename not in df:
                df[bvi.dest[-1].scopename] = set()
            _collect_dataflow(bvi.tree, df[bvi.dest[-1].scopename])
    return df


class CollectUtils(RepairTemplate):
    def __init__(self, name: str):
        super().__init__(name)

        self.assignment = []
        self.blocking_assignment = []
        self.nonblocking_assignment = []
        self.cond_vars = []
        self.ops = []

    def visit_Power(self, node: vast.Power):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Times(self, node: vast.Times):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Divide(self, node: vast.Divide):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Mod(self, node: vast.Mod):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Plus(self, node: vast.Plus):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Minus(self, node: vast.Minus):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Sll(self, node: vast.Sll):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Srl(self, node: vast.Srl):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Sla(self, node: vast.Sla):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Sra(self, node: vast.Sra):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_LessThan(self, node: vast.LessThan):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_GreaterThan(self, node: vast.GreaterThan):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_LessEq(self, node: vast.LessEq):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_GreaterEq(self, node: vast.GreaterEq):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Eq(self, node: vast.Eq):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_NotEq(self, node: vast.NotEq):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Eql(self, node: vast.Eql):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_NotEql(self, node: vast.NotEql):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_And(self, node: vast.And):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Xor(self, node: vast.Xor):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    # def visit_Xor(self, node: vast.Xor):
    #     self.ops.append(node.__class__)
    #     self.generic_visit(node)
    #     return node

    def visit_Xnor(self, node: vast.Xnor):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Or(self, node: vast.Or):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Land(self, node: vast.Land):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Lor(self, node: vast.Lor):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Ulnot(self, node: vast.Ulnot):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Unot(self, node: vast.Unot):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Uand(self, node: vast.Uand):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Unand(self, node: vast.Unand):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Uor(self, node: vast.Uor):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Unor(self, node: vast.Unor):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Uxor(self, node: vast.Uxor):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Uxnor(self, node: vast.Uxnor):
        self.ops.append(node.__class__)
        self.generic_visit(node)
        return node

    def visit_Assign(self, node: vast.Assign):
        self.assignment.append(node)
        self.generic_visit(node)
        return node

    def visit_BlockingSubstitution(self, node: vast.BlockingSubstitution):
        self.blocking_assignment.append(node)
        self.generic_visit(node)
        return node

    def visit_NonblockingSubstitution(self, node: vast.NonblockingSubstitution):
        self.nonblocking_assignment.append(node)
        self.generic_visit(node)
        return node

    def visit_IfStatement(self, node: vast.IfStatement):
        vars = get_rhs_vars(node.cond)
        self.cond_vars.extend(vars)
        self.generic_visit(node)
        return node


def collect_blocks(ast: vast.Source):
    cu = CollectUtils(name='collect_util')
    cu.visit(ast)
    return cu


_synth_var_prefix = "__synth_"
_synth_change_prefix = "__synth_change_"


class InsertAnchor(RepairTemplate):
    def __init__(self, name: str, en_always, en_if, en_case, vars, assignment: [], blocking_assignment: [],
                 nonblocking_assignment: []):
        super().__init__(name)

        self.vars = vars
        self.en_always = en_always
        self.en_if = en_if
        self.en_case = en_case
        self.assignment = assignment
        self.blocking_assignment = blocking_assignment
        self.nonblocking_assignment = nonblocking_assignment

        self._in_proc = False
        self._in_blocking = False

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

        # declare synthesis vars
        decls = self._declare_synth_regs()
        mod_def: vast.ModuleDef = ast.description.definitions[0]
        mod_def.items = tuple(decls + list(mod_def.items))

    def gen_plausible_body(self, orig: vast.Case):
        s_case = deepcopy(orig)
        # not all is needed.

        if isinstance(s_case.statement, vast.Block):
            alters = []
            for i in range(len(s_case.statement.statements)):
                alters.append(vast.IfStatement(
                    vast.Identifier(self.make_synth_var(1)),
                    deepcopy(s_case.statement.statements[i]),
                    None
                ))
            s_case.statement.statements = tuple(alters)
        else:
            s_case.statement = vast.IfStatement(
                vast.Identifier(self.make_synth_var(1)),
                s_case.statement,
                None
            )
        return s_case

    def visit_BlockingSubstitution(self, node: vast.BlockingSubstitution):
        # self.blocking_assignment[node.left] = node
        return node

    def visit_NonblockingSubstitution(self, node: vast.NonblockingSubstitution):
        # self.nonblocking_assignment[node.left] = node
        return node

    def get_assign_block(self, node, except_vars=[]):
        node = deepcopy(node)
        analysis = ProcessAnalyzer()
        analysis.run(node)
        assigned_vars = [var for var in analysis.assigned_vars if isinstance(var, vast.Identifier) and var not in except_vars]

        def gen_assignments(assigned_vars, analysis):
            stmts = []
            for var in assigned_vars:
                lvars = get_lvars(var)
                filtered_case_inputs = filter_atom(analysis.case_inputs, lvars, self.vars)
                if len(filtered_case_inputs) > 0:
                    width = get_lhs_width(var, self.vars)
                    const = vast.Identifier(self.make_synth_var(width))
                    # if node.sens_list.list[0].type == 'posedge' or node.sens_list.list[0].type == 'negedge':
                    if not self._in_blocking:
                        assign = vast.NonblockingSubstitution(vast.Lvalue(var), vast.Rvalue(const))
                    else:
                        assign = vast.BlockingSubstitution(vast.Lvalue(var), vast.Rvalue(const))

                    # inner = vast.IfStatement(vast.Identifier(self.make_synth_var(1)), assign, None)
                    stmts.append(self.make_change_stmt(assign, 0))
            blk = vast.Block(statements=stmts)
            return blk
        return gen_assignments(assigned_vars, analysis)

    def visit_Always(self, node: vast.Always):
        if node.sens_list.list[0].type == 'posedge' or node.sens_list.list[0].type == 'negedge':
            self._in_blocking = True

        self._in_proc = True
        if not self.en_always:
            self.visit(node.statement)
            self._in_proc = False
            self._in_blocking = False
            return node
        # add if statement ahead of always

        # do not only use the variable in the block
        # self.nonblocking_assignment = {}
        # self.blocking_assignment = {}
        self.visit(node.statement)

        # alter_assignment = []
        # if node.sens_list.list[0].type == 'posedge' or node.sens_list.list[0].type == 'negedge':
        #     alter_assignment = self.nonblocking_assignment
        # else:
        #     alter_assignment = self.blocking_assignment


        body = self.get_assign_block(node)

        if isinstance(node.statement, vast.Block):
            node.statement.statements = (body, *list(node.statement.statements),)
        else:
            node.statement = vast.Block(statements=[body, node.statement])

        self._in_proc = False
        self._in_blocking = False
        return node

    def visit_IfStatement(self, node: vast.IfStatement):
        if not self._in_proc:
            return node
        if not self.en_if:
            self.visit(node.true_statement)
            self.visit(node.false_statement)
            return node
        # add if branch at the end of if statement
        synth_branch = self.visit(deepcopy(node.true_statement))
        node.true_statement = self.visit(node.true_statement)
        if node.false_statement is None:
            node.false_statement = vast.IfStatement(
                cond=vast.Identifier(self.make_synth_var(1)),
                true_statement=synth_branch,
                false_statement=self.visit(node.false_statement)
            )
        else:
            node.false_statement = self.visit(node.false_statement)
        return node

    def visit_CaseStatement(self, node: vast.CaseStatement):
        if not self.en_case:
            for i in range(len(node.caselist)):
                self.visit(node.caselist[i].statement)
            return node

        # add case arm ahead of caselist
        # add default arm at the end of caselist
        first_case_body = deepcopy(node.caselist[0])
        # s_case = self.gen_plausible_body(node.caselist[0])

        # node.caselist = (s_case, *list(node.caselist),)
        # end
        if node.caselist[-1].cond is not None:
            node.caselist = (*node.caselist, vast.Case(cond=None,
                                                       statement=vast.Block(statements=[first_case_body.statement]))
                             )

        # first_case_body = self.gen_plausible_body(first_case_body).statement

        # generate assignments for default case, remove the variables in the comp.
        body = self.get_assign_block(node, except_vars=[node.comp])
        for i in range(len(node.caselist)):
            if i == 0:
                continue
            if node.caselist[i].cond is None:
                blk = vast.Block(
                    statements=[vast.IfStatement(
                        cond=vast.Eq(
                            left=node.comp,
                            right=vast.Identifier(self.make_synth_var(get_rhs_width(node.comp, self.vars)))
                        ),
                        true_statement=body,
                        false_statement=None)
                    ]
                )

                default_blk = vast.IfStatement(cond=vast.Identifier(self.make_change_var()),
                                               true_statement=blk, false_statement=None)
                node.caselist[i].statement = vast.Block(
                    statements=[
                        default_blk,
                        vast.IfStatement(cond=vast.Identifier(self.make_change_var()),
                                         true_statement=node.caselist[i].statement,
                                         false_statement=None)
                    ]
                )
            else:
                self.visit(node.caselist[i].statement)

        return node


def insert_anchor(
        ast: vast.Source,
        en_always,
        en_if,
        en_case,
        vars,
        assignment=None,
        blocking_assignment=None,
        nonblocking_assignment=None
):
    if nonblocking_assignment is None:
        nonblocking_assignment = []
    if blocking_assignment is None:
        blocking_assignment = []
    if assignment is None:
        assignment = []
    cu = InsertAnchor('insert_anchor',
                      en_always,
                      en_if,
                      en_case,
                      vars,
                      assignment, blocking_assignment, nonblocking_assignment)
    namespace = Namespace(ast)
    cu.apply(namespace, ast)
    return ast
