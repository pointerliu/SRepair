# Copyright 2022 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>
from copy import deepcopy
from typing import List, Dict, Set

from pyverilog.utils.identifierreplace import children_items
from rtlrepair.repair import RepairTemplate
from rtlrepair.analysis import AnalysisResults, VarInfo
from rtlrepair.snn_templates.utils import get_dataflow, analysis_if_body, collect_blocks, insert_anchor, get_lhs_width, \
    get_lhs_vars
from rtlrepair.utils import Namespace
import pyverilog.vparser.ast as vast

_synth_var_prefix = "__synth_"
_synth_change_prefix = "__synth_change_"


def edge_flip(ast: vast.Source, analysis: AnalysisResults):
    namespace = Namespace(ast)
    repl = EdgeFlip(analysis.vars, analysis.widths)
    repl.apply(namespace, ast)
    return repl.change_count


class EdgeFlip(RepairTemplate):
    def __init__(
            self,
            vars: dict[str, VarInfo],
            widths: dict[vast.Node, int],
    ):
        super().__init__(name="replace_atom")
        self.vars = vars
        self.widths = widths
        self._in_proc = False
        self._sync_proc = False
        self._in_proc_always: vast.Always = None
        self.change_count = 0

        self.namespace_id = 0

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

    def visit_Always(self, node: vast.Always):
        self._in_proc = True
        self._in_proc_always = node
        if node.sens_list.list[0].type == 'posedge':
            self._sync_proc = True
            node.sens_list.list[0].type = 'negedge'
        elif node.sens_list.list[0].type == 'negedge':
            self._sync_proc = True
            node.sens_list.list[0].type = 'posedge'

        node.statement = self.visit(node.statement)
        self._in_proc = False
        return node

    def visit_BlockingSubstitution(self, node: vast.BlockingSubstitution):
        if self._in_proc and self._sync_proc:
            gen = vast.NonblockingSubstitution(left=deepcopy(node.left), right=deepcopy(node.right))
            gen = self.visit(gen)
            return gen
        return node

    def visit_NonblockingSubstitution(self, node: vast.NonblockingSubstitution):
        if self._in_proc and not self._sync_proc:
            self._in_proc_always.sens_list.list[0].type = 'posedge'
            self.change_count += 1
        return node
