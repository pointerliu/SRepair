# Copyright 2022-2024 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>
import math

import pyverilog.vparser.ast as vast
from rtlrepair.utils import Namespace, serialize, parse_width, parse_verilog_int_literal
from rtlrepair.visitor import AstVisitor

_synth_var_prefix = "__synth_"
_synth_change_prefix = "__synth_change_"


def is_change_var(ident: vast.Node) -> bool:
    return isinstance(ident, vast.Identifier) and ident.name.startswith(_synth_change_prefix)

def is_synth_var(ident: vast.Node) -> bool:
    return isinstance(ident, vast.Identifier) and ident.name.startswith(_synth_var_prefix)


def _make_any_const(name: str, width: int) -> vast.Decl:
    assert width >= 1
    width_node = None if width == 1 else vast.Width(vast.IntConst(str(width - 1)), vast.IntConst("0"))
    return vast.Decl((
        vast.Reg(name, width=width_node),
        vast.Assign(
            left=vast.Lvalue(vast.Identifier(name)),
            right=vast.Rvalue(vast.SystemCall("anyconst", []))
        )
    ))


class RepairTemplate(AstVisitor):
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.changed = []
        self.synth_vars = []
        self._namespace = None

        self._in_gen_blk = False

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

    def _declare_synth_regs(self) -> list:
        syms = [(name, 1) for name in self.changed] + self.synth_vars
        return [_make_any_const(name, width) for name, width in syms]

    def make_change(self, changed_expr: vast.Node, original_expr: vast.Node):
        name: str = self._namespace.new_name(_synth_change_prefix + self.name)
        self.changed.append(name)
        return vast.Cond(vast.Identifier(name), changed_expr, original_expr, lineno=original_expr.lineno)

    def make_change_var(self):
        name: str = self._namespace.new_name(_synth_change_prefix + self.name)
        self.changed.append(name)
        return name

    def make_change_stmt(self, change_stmt: vast.Node, lineno: int):
        name: str = self._namespace.new_name(_synth_change_prefix + self.name)
        self.changed.append(name)
        return vast.IfStatement(vast.Identifier(name), change_stmt, None, lineno=lineno)

    def make_synth_var(self, width: int):
        assert width >= 1
        name = self._namespace.new_name(_synth_var_prefix + self.name)
        self.synth_vars.append((name, width))
        return name

    def make_inversion(self, expr: vast.Node, free: bool = False, width: int = 1):
        """ generates an optional inversion of a boolean condition """
        do_invert = self.make_synth_var(width) if free else self.make_change_var()
        may_invert = vast.Xor(vast.Identifier(do_invert), expr)
        return may_invert

    def make_choice(self, exprs: list):
        """ allows the synthesizer so choose one expression """
        assert len(exprs) > 0
        if len(exprs) == 1:
            return exprs[0]
        # select one expression
        select_width = int(math.ceil(math.log2(len(exprs))))
        selector = vast.Identifier(self.make_synth_var(select_width))
        out = exprs[0]
        for ii, other in enumerate(exprs[1:]):
            ident = vast.IntConst(f"{select_width}'b{ii:b}")
            out = vast.Cond(vast.Eq(selector, ident), other, out)
        return out

    def visit_Decl(self, node: vast.Decl):
        # the only nodes we want to visit by default are wire assignment which result from statements like:
        # wire x = 'd1;
        wires = set()
        children = []
        for child in node.list:
            if isinstance(child, vast.Wire):
                wires.add(child.name)
                children.append(child)
            elif (isinstance(child, vast.Assign) and
                  isinstance(child.left, vast.Lvalue) and
                  isinstance(child.left.var, vast.Identifier) and
                  child.left.var.name in wires):
                  # visit wires assignments
                children.append(self.visit(child))
            else:
                children.append(child)

        pass

    def visit_Wire(self, node: vast.Wire):
        # by default we ignore any wire declarations
        return node

    def visit_Reg(self, node: vast.Reg):
        # by default we ignore any reg declarations
        return node

    def visit_Input(self, node: vast.Input):
        # by default we ignore any input declarations
        return node

    def visit_Output(self, node: vast.Output):
        # by default we ignore any output declarations
        return node

    def visit_Inout(self, node: vast.Inout):
        # by default we ignore any inout declarations
        return node

    def visit_Instance(self, node: vast.Instance):
        # TODO: it would be OK to visit instance connections that are inputs to the instance
        return node

    def visit_Parameter(self, node: vast.Parameter):
        # by default we ignore any parameter declarations
        return node

    def visit_ParamArg(self, node: vast.ParamArg):
        # by default we ignore any parameter assignments since they need to be constant
        return node

    def visit_Integer(self, node: vast.Integer):
        # by default we ignore any integer declarations
        return node

    def visit_Lvalue(self, node: vast.Lvalue):
        # by default we ignore any lvalues
        return node

    def visit_Portlist(self, node: vast.Portlist):
        # by default we ignore the portlist since we cannot dynamically change ports
        return node

    def visit_Initial(self, node: vast.Initial):
        # by default we ignore the initial statements since starting values of registers cannot change at circuit run time
        return node

    def visit_ForStatement(self, node: vast.ForStatement):
        # by default we ignore the condition, pre and post of the for statement since it cannot dynamically be changed
        node.statement = self.visit(node.statement)
        return node

    def visit_SensList(self, node: vast.SensList):
        # by default we ignore the sens list since we cannot put dynamic values into that
        return node

    def visit_Pointer(self, node: vast.Pointer):
        # by default we ignore the variable (but not the offset, aka ptr) of an array access
        node.ptr = self.visit(node.ptr)
        return node

    def visit_Partselect(self, node: vast.Partselect):
        # by default we ignore part selects (aka bit slices) since the integer indices are constants and messing with
        # the variable might also not be a good idea
        return node

    def visit_IndexedPartselect(self, node: vast.IndexedPartselect):
        # by default, we ignore the stride of an indexed part select
        node.base = self.visit(node.base)
        return node

    def visit_Repeat(self, node: vast.Repeat):
        # by default we ignore the times attribute of a repeat since it needs to be a constant
        node.value = self.visit(node.value)
        return node

    def visit_DelayStatement(self, node: vast.DelayStatement):
        # by default, we ignore delay statement since they do not make much sense for synchronous circuit descriptions
        return node

    def visit_GenerateStatement(self, node: vast.GenerateStatement):
        self._in_gen_blk = True
        for s in node.items:
            self.visit(s)
        self._in_gen_blk = False
        return node

    # def visit_GenerateStatement(self, node: vast.GenerateStatement):
    #     # generate blocks have their own rules which disallow many of the usual instrumentation that we do
    #     # in the future, one might try to find a small set of changes that might be allowed
    #     return node


def do_repair(ast: vast.Source, assignment: dict, blockified: list) -> list:
    """ applies the repair generated by the synthesizer and returns a list of changes """
    # we need to remove any hierarchical suffixes from the assignment names since we will be operating on a single
    # module directly
    assignment = { n.split('.')[-1]: v for n,v in assignment.items() }
    changes = RepairPass(blockified).run(ast, assignment)

    # sanity check the number of changes against the number of change variables that are set to 1
    change_count = sum(v for n,v in assignment.items() if n.startswith(_synth_change_prefix))
    # assert len(changes) == change_count, f"changes might be miscounted: {len(changes)} != {change_count} (# change vars set to 1)"

    return changes


_empty_block = vast.Block(tuple([]))

def is_value(node: vast.Node, value: int) -> bool:
    return isinstance(node, vast.IntConst) and parse_verilog_int_literal(node.value)[0] == value

class RepairPass(AstVisitor):
    """ repairs an AST by applying the assignment generated by the synthesizer """

    def __init__(self, blockified: list = None):
        super().__init__()
        self.assignment = dict()
        self.width = dict()
        self.changes = []
        self.blockified = set() if blockified is None else set(blockified)

    def run(self, ast: vast.Source, assignment: dict):
        self.changes = []
        self.assignment = assignment
        self.width = self._remove_synth_var_decl(ast)
        self.visit(ast)
        return self.changes

    def _remove_synth_var_decl(self, ast: vast.Source) -> dict:
        width = dict()
        mod_def: vast.ModuleDef = ast.description.definitions[0]
        items = []
        for entry in mod_def.items:
            is_synth_var = (
                    isinstance(entry, vast.Decl) and
                    isinstance(entry.list[0], vast.Reg) and
                    entry.list[0].name in self.assignment
            )

            if is_synth_var:
                assert len(entry.list) == 2
                reg = entry.list[0]
                width[reg.name] = parse_width(reg.width)
            else:
                items.append(entry)
        mod_def.items = tuple(items)
        return width

    def visit_Cond(self, node: vast.Cond):
        if is_synth_var(node.cond):
            return self.visit_change_node(node)
        # match "make_choice" pattern
        if isinstance(node.cond, vast.Eq) and is_synth_var(node.cond.left):
            assert not is_change_var(node.cond.left), "unexpected change var in condition"
            assert isinstance(node.cond.right, vast.IntConst)
            (expected, _) = parse_verilog_int_literal(node.cond.right.value)
            actual = self.get_synth_var_value(node.cond.left)
            if expected == actual:
                return self.visit(node.true_value)
            else:
                return self.visit(node.false_value)
        return self.generic_visit(node)

    def visit_IfStatement(self, node: vast.IfStatement):
        return self.visit_change_node(node)

    def visit_Xor(self, node: vast.Xor):
        if not is_synth_var(node.left):
            return self.generic_visit(node)
        value = self.get_synth_var_value(node.left)
        expr = self.visit(node.right)
        if value == 0:
            return expr
        else:
            # changed = vast.Ulnot(expr)
            changed = vast.Unot(expr)
            if is_change_var(node.left):
                self.record_change(node.lineno, expr, changed)
            return changed

    def visit_And(self, node: vast.And):
        return self.visit_bin_op(node, 1)

    def visit_Or(self, node: vast.Or):
        return self.visit_bin_op(node, 0)


    def visit_bin_op(self, node, identity_value: int):
        assert isinstance(node, vast.Or) or isinstance(node, vast.And)

        # first check if there are any change conditions
        left_is_cond = isinstance(node.left, vast.Cond) and is_change_var(node.left.cond)
        right_is_cond = isinstance(node.right, vast.Cond) and is_change_var(node.right.cond)

        # now we can visit
        visited = self.generic_visit(node)
        assert isinstance(visited, vast.Or) or isinstance(visited, vast.And)
        if not left_is_cond and not right_is_cond:
            return visited

        # simplify only change conditions
        if left_is_cond and is_value(visited.left, identity_value):
            return visited.right
        if right_is_cond and is_value(visited.right, identity_value):
            return visited.left
        return visited


    def get_synth_var_value(self, ident: vast.Identifier) -> int:
        assert is_synth_var(ident)
        if ident.name in self.assignment:
            return self.assignment[ident.name]
        else:
            # sometimes a synthesis var seems to be optimized out, or we do not get the assignment for another reason
            return 0


    def visit_change_node(self, node):
        """ unified change function for statement and expression changes
            implements synthesizer choice (created by make_change or make_change_stmt)
        """
        assert isinstance(node, vast.IfStatement) or isinstance(node, vast.Cond)
        if not is_synth_var(node.cond):
            if is_value(node.cond, 1) or not isinstance(node, vast.IfStatement):
                return self.generic_visit(node)
            else:
                # check to see if the condition simplifies to one (because it was a combination of change variables)
                node = self.generic_visit(node)
                if is_value(node.cond, 1):
                    return node.true_statement
                else:
                    return node
        # we found a synthesis change, now we need to plug in the original or the old expression
        value = self.get_synth_var_value(node.cond)
        if isinstance(node, vast.Cond):
            false_node, true_node = node.false_value, node.true_value
        else:
            false_node, true_node = node.false_statement, node.true_statement
        if value == 1:
            changed = self.visit(true_node)
            # record the change if we are dealing with a change var
            if is_change_var(node.cond):
                self.record_change(node.lineno, false_node, changed)
            return changed
        else:
            visited = self.visit(false_node)
            # if we return None, the node is not removed, instead the original node is retained :(
            if visited is None:
                return _empty_block
            return visited

    def record_change(self, line: int, old: vast.Node, new: vast.Node):
        self.changes.append((str(line), serialize(old), serialize(new)))


    def visit_Identifier(self, node: vast.Identifier):
        """ substitute synthesis variable with value """
        if node.name not in self.assignment:
            return node
        value = self.assignment[node.name]
        width = self.width[node.name]
        prefix = "" if width is None else str(width)
        return vast.IntConst(f"{prefix}'b{value:b}")

    def visit_Block(self, node: vast.Block):
        # first we visit all children as this might remove statements in the block
        node = self.generic_visit(node)
        # then we check to see if the block can be removed:
        # 1) if there are multiple statements in the block, it is required
        if len(node.statements) > 1:
            return node
        # 2) if the block was added by the repair template --> remove it
        elif id(node) in self.blockified:
            assert len(node.statements) > 0
            return node.statements[0]
        # 3) if it seems like the original already contained this block --> retain it
        else:
            return node
