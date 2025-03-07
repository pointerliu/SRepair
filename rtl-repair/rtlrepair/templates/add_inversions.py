# Copyright 2022 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>

from rtlrepair.repair import RepairTemplate
from rtlrepair.analysis import AnalysisResults, VarInfo
from rtlrepair.utils import Namespace
import pyverilog.vparser.ast as vast


def add_inversions(ast: vast.Source, analysis: AnalysisResults):
    namespace = Namespace(ast)
    Inverter(analysis.widths).apply(namespace, ast)


_skip_nodes = {vast.Lvalue, vast.Decl, vast.SensList, vast.Portlist}
_skip_children_nodes = {vast.Partselect, vast.Repeat, vast.Pointer}


class Inverter(RepairTemplate):
    def __init__(self, widths: dict):
        super().__init__(name="invert")
        self.widths = widths

    def generic_visit(self, node):
        # skip nodes that contain declarations or senselists
        if type(node) in _skip_nodes:
            return node
        # ignore constants as they are already covered by the literal replacer template
        if isinstance(node, vast.Constant):
            return node
        # some nodes children should not be messed with since it easily leads to incorrect Verilog
        if not type(node) in _skip_children_nodes:
            # visit all children
            node = super().generic_visit(node)
        # if it is a 1-bit node, add the possibility to invert
        if node in self.widths and self.widths[node] == 1:
            # add possibility to invert boolean expression
            node = self.make_change(vast.Ulnot(node), node)
        return node

    # TODO: this is to fix a bug with the generic visitor not being called.
    def visit_Repeat(self, node: vast.Repeat):
        return node
