# Copyright 2022 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>
from copy import deepcopy
from typing import List, Dict, Set

from pyverilog.utils.identifierreplace import children_items
from rtlrepair.repair import RepairTemplate
from rtlrepair.analysis import AnalysisResults, VarInfo
from rtlrepair.snn_templates.utils import get_dataflow, analysis_if_body, collect_blocks, insert_anchor, get_lhs_width, \
    get_lhs_vars, get_rhs_width
from rtlrepair.utils import Namespace
import pyverilog.vparser.ast as vast

_synth_var_prefix = "__synth_"
_synth_change_prefix = "__synth_change_"


def type_voting(ast: vast.Source, analysis: AnalysisResults):
    namespace = Namespace(ast)
    repl = TypeVoting(analysis.vars, analysis.widths, analysis.width_voting)
    return repl.run()


class TypeVoting(RepairTemplate):
    def __init__(
            self,
            vars: dict[str, VarInfo],
            widths: dict[vast.Node, int],
            width_voting: dict
    ):
        super().__init__(name="replace_atom")
        self.vars = vars
        self.widths = widths
        self.namespace_id = 0
        self._sync_proc = False
        self.width_voting = width_voting

        self.node_replace = {}

    def run(self):
        change_count = 0
        for var_name in self.width_voting:

            if len(self.width_voting[var_name]) >= 2:

                self.width_voting[var_name] = dict(
                    sorted(self.width_voting[var_name].items(), key=lambda item: len(item[1]), reverse=True))
                _a = 1
                vot_width = 0
                for i, key in enumerate(self.width_voting[var_name]):
                    if i == 0:
                        vot_width = key
                        continue
                    if len(self.width_voting[var_name][key]) >= len(self.width_voting[var_name][vot_width]):
                        continue
                    for node in self.width_voting[var_name][key]:
                        if isinstance(node, vast.Output):
                            node.width = vast.Width(lsb=vast.IntConst(value='0'),
                                                    msb=vast.IntConst(value=str(vot_width - 1)))
                            change_count += 1
                        elif isinstance(node, vast.IntConst):
                            const_w = node.value.split("'")
                            if len(const_w) > 1:
                                node.value = str(vot_width) + "'" + const_w[1]
                                change_count += 1

        return change_count
