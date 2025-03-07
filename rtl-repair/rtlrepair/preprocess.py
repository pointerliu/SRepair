# Copyright 2022 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>
import os
import shutil
import re
from dataclasses import dataclass
from pathlib import Path
import subprocess

from benchmarks import Benchmark, get_other_sources
from rtlrepair import parse_verilog, serialize
from rtlrepair.analysis import analyze_ast
from rtlrepair.snn_templates import type_voting, edge_flip
from rtlrepair.utils import ensure_block
from rtlrepair.visitor import AstVisitor
import pyverilog.vparser.ast as vast


def preprocess(working_dir: Path, benchmark: Benchmark) -> (Path, int):
    """ runs a linter on the verilog file and tries to address some issues """
    # create directory
    assert working_dir.exists()
    include = benchmark.design.directory
    assert include is None or include.exists()
    preprocess_dir = working_dir / "0_preprocess"
    if preprocess_dir.exists():
        shutil.rmtree(preprocess_dir)
    os.mkdir(preprocess_dir)

    # run linter up to four times
    change_count = 0
    previous_warnings = []
    other_files = get_other_sources(benchmark)
    filename = benchmark.bug.buggy
    for ii in range(6):
        warnings = run_linter(ii, filename, other_files, preprocess_dir, include)

        # for now we ignore all warnings that are not part of the repair file
        warnings = [w for w in warnings if w.filename.name == filename.name]

        # if change_count > 0:
        # check to see if warnings actually changed or if we are at a fixed point
        # if _same_warnings(previous_warnings, warnings):
        #     break

        # changed = True
        # parse ast and fix if necessary
        fixed_filename = preprocess_dir / f"{filename.stem}.{ii}.v"
        ast = parse_verilog(filename, include)

        if ii == 0:
            # analysis = analyze_ast(ast)
            # change_count += edge_flip(ast, analysis)
            continue
        elif ii == 1:
            # type voting
            analysis = analyze_ast(ast)
            # change_count += type_voting(ast, analysis)
        else:
            if len(warnings) == 0:
                break  # no warnings -> nothing to fix

            try:
                fixer = LintFixer(warnings)
                change_count += fixer.apply(ast)
            except RuntimeWarning as e:
                continue

        with open(fixed_filename, "w") as f:
            f.write(serialize(ast))
        filename = fixed_filename
        previous_warnings = warnings

    # return path to preprocessed file
    return filename, change_count


def _same_warnings(old: list, new: list) -> bool:
    return {_warning_sig(w) for w in old} == {_warning_sig(w) for w in new}


def _check_for_verilator():
    r = subprocess.run(["verilator", "-version"], stdout=subprocess.PIPE)
    assert r.returncode == 0, "failed to find verilator"


# while WIDTH warnings can be indicative of a bug, they are generally too noisy to deal with easily
# CASEOVERLAP might be an interesting warning to deal with
_ignore_warnings = {"DECLFILENAME", "ASSIGNDLY", "UNUSED", "EOFNEWLINE", "WIDTH", "CASEOVERLAP", "STMTDLY",
                    "TIMESCALEMOD", "MULTIDRIVEN", "UNDRIVEN", "LITENDIAN"}
_verilator_lint_flags = ["--lint-only", "-Wno-fatal", "-Wall"] + [f"-Wno-{w}" for w in _ignore_warnings]
_verilator_re = re.compile(r"%Warning-([A-Z]+): ([^:]+):(\d+):(\d+):([^\n]+)")


def remove_blank_lines(lines: list) -> list:
    return [ll.strip() for ll in lines if len(ll.strip()) > 0]


@dataclass
class LintWarning:
    tpe: str
    filename: Path
    line: int
    col: int
    msg: str


def _warning_sig(warn: LintWarning) -> str:
    return f"{warn.tpe}@{warn.line}"


def parse_linter_output(lines: list) -> list:
    out = []
    for line in lines:
        m = _verilator_re.search(line)
        if m is not None:
            (tpe, filename, line, col, msg) = m.groups()
            out.append(LintWarning(tpe, Path(filename), int(line), int(col), msg.strip()))
        elif len(out) > 0:
            out[0].msg += "\n" + line
    return out


def run_linter(iteration: int, filename: Path, other_files: list[Path], preprocess_dir: Path, include: Path) -> list:
    """ Things we are interested in:
        - ASSIGNDLY: Unsupported: Ignoring timing control on this assignment
        - CASEINCOMPLETE: Case values incompletely covered (example pattern 0x5)
          - we might need to fix this to get the actual latch warning from verilator...
        - BLKSEQ: Blocking assignment '=' in sequential logic process
        - LATCH: Latch inferred for signal 'fsm_full.next_state'
                 (not all control paths of combinational always assign a value)
        - BLKANDNBLK: Unsupported: Blocked and non-blocking assignments to same variable: 'fsm_full.state'
    """
    _check_for_verilator()
    cmd = ["verilator"] + _verilator_lint_flags
    if include is not None:
        cmd += [f"-I{include.resolve()}"]
    cmd += (str(f.resolve()) for f in [filename] + other_files)
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    info = (r.stdout + r.stderr).decode('utf-8').splitlines()
    info = remove_blank_lines(info)
    if len(info) == 0:
        return []
    # output raw info
    with open(preprocess_dir / f"{iteration}_linter.txt", "w") as f:
        f.write("\n".join(info) + "\n")
    # parse
    return parse_linter_output(info)


_fix_warnings = {"CASEINCOMPLETE", "BLKSEQ", "LATCH", "COMBDLY"}


def filter_warnings(warnings: list) -> list:
    out = []
    for warn in warnings:
        if warn.tpe in _fix_warnings:
            out.append(warn)
        elif warn.tpe not in _ignore_warnings:
            raise RuntimeWarning(f"Unknown warning type: {warn}")
    return out


_latch_re = re.compile(r"Latch inferred for signal '([^']+)'")

# TODO: maybe change back to 0
_default_value = "'d0"


def assign_latch_signal(latch_warning: LintWarning):
    m = _latch_re.search(latch_warning.msg)
    assert m is not None, latch_warning.msg
    signal_parts = m.group(1).split(".")
    ident = vast.Identifier(signal_parts[-1].strip())
    return vast.BlockingSubstitution(vast.Lvalue(ident), vast.Rvalue(vast.IntConst(_default_value)))


class LintFixer(AstVisitor):
    """ This class addressed the following lint warning:
        - CASEINCOMPLETE: Case values incompletely covered (example pattern 0x5)
        - LATCH
        - BLKSEQ: Blocking assignment '=' in sequential logic process
        - COMBDLY: Non-blocking assignment \'<=\' in combinational logic process
    """

    def __init__(self, warnings: list):
        super().__init__()
        self.warnings = filter_warnings(warnings)
        self.change_count = 0

    def _find_warnings(self, tpe: str, line: int):
        out = []
        for warn in self.warnings:
            if warn.tpe == tpe and warn.line == line:
                out.append(warn)
        return out

    def apply(self, ast: vast.Source) -> int:
        self.change_count = 0
        self.visit(ast)
        return self.change_count

    def visit_CaseStatement(self, node: vast.CaseStatement):
        node = self.generic_visit(node)
        # add empty default case to fix incomplete cases (this will reveal LATCH warnings in verilator)
        if len(self._find_warnings("CASEINCOMPLETE", node.lineno)) > 0:
            default = vast.Case(None, vast.Block(tuple([])))
            node.caselist = tuple(list(node.caselist) + [default])
            self.change_count += 1
        return node

    def visit_Always(self, node: vast.Always):
        node = self.generic_visit(node)
        # add a default assignment if a latch is unintentionally created
        latches = self._find_warnings("LATCH", node.lineno)
        if len(latches) == 0:
            return node
        assignments = [assign_latch_signal(ll) for ll in latches]
        stmt = ensure_block(node.statement)
        stmt.statements = tuple(assignments + list(stmt.statements))
        node.statement = stmt
        self.change_count += len(assignments)
        return node

    def visit_BlockingSubstitution(self, node: vast.BlockingSubstitution):
        node = self.generic_visit(node)
        # change to non-blocking if we got a blocking assignment in sequential logic process
        if len(self._find_warnings("BLKSEQ", node.lineno)) > 0:
            node = vast.NonblockingSubstitution(node.left, node.right, node.ldelay, node.rdelay, node.lineno)
            self.change_count += 1
        return node

    def visit_NonblockingSubstitution(self, node: vast.NonblockingSubstitution):
        node = self.generic_visit(node)
        # change to blocking if we got a non-blocking assignment in combinatorial logic process
        if len(self._find_warnings("COMBDLY", node.lineno)) > 0:
            node = vast.BlockingSubstitution(node.left, node.right, node.ldelay, node.rdelay, node.lineno)
            self.change_count += 1
        return node
