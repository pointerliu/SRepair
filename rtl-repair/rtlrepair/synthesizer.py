# Copyright 2022 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>

import subprocess
import json
from dataclasses import dataclass
from pathlib import Path

from benchmarks import Benchmark, TraceTestbench, get_other_sources
from rtlrepair.utils import _root_dir, serialize, Status, status_name_to_enum
import pyverilog.vparser.ast as vast
from benchmarks.yosys import to_btor

# the synthesizer is written in rust, the source code lives in src
_bin_rel = Path("target") / "release" / "synth"
_synthesizer_dir = _root_dir / "synth"
_bin = _synthesizer_dir / _bin_rel


# old Scala synthesizer, the source code lives in src
_jar_rel = Path("target") / "scala-2.13" / "bug-fix-synthesizer-assembly-0.1.jar"
_jar = _root_dir / "synthesizer" / _jar_rel


@dataclass
class SynthOptions:
    solver: str
    init: str
    incremental: bool
    verbose: bool
    past_k_step_size: int = None
    old_synthesizer: bool = False


@dataclass
class SynthStats:
    solver_time_ns: int
    past_k: int
    future_k: int


def _check_bin():
    assert _bin.exists(), f"Failed to find synth binary, did you run cargo build --release?\n{_bin}"

def _check_jar():
    assert _jar.exists(), f"Failed to find JAR, did you run sbt assembly?\n{_jar}"


def _run_synthesizer(working_dir: Path, design: Path, testbench: Path, opts: SynthOptions) -> dict:
    assert design.exists(), f"{design=} does not exist"
    assert testbench.exists(), f"{testbench=} does not exist"
    if opts.old_synthesizer:
        _check_jar()
    else:
        _check_bin()
    args = ["--design", str(design), "--testbench", str(testbench), "--solver", opts.solver, "--init", opts.init]
    if opts.incremental:
        args += ["--incremental"]
    if opts.verbose:
        args += ["--verbose"]
    if opts.past_k_step_size:
        args += ["--past-k-step-size", str(opts.past_k_step_size)]
    args += ["--max-incorrect-solutions-per-window-size", str(32)]
    # test: multiple solutions
    # args += ["--sample-solutions", "2"]
    if opts.old_synthesizer:
        cmd = ["java", "-cp", _jar, "synth.Synthesizer"]
    else:
        cmd = [_bin]
    cmd += args
    cmd_str = ' '.join(str(p) for p in cmd)  # for debugging

    # write command to file in order to be able to reproduce the failed synthesis command
    with open(working_dir / "run_synth.sh", 'w') as ff:
        print("#!/usr/bin/env bash", file=ff)
        print(cmd_str, file=ff)

    cmd[0] = str(cmd[0])
    # print(' '.join(cmd))


    r = subprocess.run(cmd, check=True, stdout=subprocess.PIPE)
    output = r.stdout.decode('utf-8')
    # command write output to file for debugging
    with open(working_dir / "synth.txt", 'w') as ff:
        print(cmd_str, file=ff)
        ff.write(output)
    try:
        # the JSON output follows the needle
        needle = "== RESULT ==\n"
        return json.loads(output.split(needle)[-1])
    except json.JSONDecodeError as e:
        print("Failed to parse synthesizer output as JSON:")
        print(r.stdout)
        raise e


class Synthesizer:
    """ generates assignments to synthesis variables which fix the design according to a provided testbench """

    def __init__(self):
        pass

    def run(self, working_dir: Path, opts: SynthOptions, instrumented_ast: vast.Source, benchmark: Benchmark) -> (
            Status, list, SynthStats):
        assert isinstance(benchmark.testbench,
                          TraceTestbench), f"{benchmark.testbench} : {type(benchmark.testbench)} is not a TraceTestbench"

        # save instrumented AST to disk so that we can call yosys
        synth_filename = working_dir / f"{benchmark.bug.buggy.stem}.instrumented.v"
        with open(synth_filename, "w") as f:
            f.write(serialize(instrumented_ast))

        # convert file and run synthesizer
        additional_sources = get_other_sources(benchmark)
        btor_filename = to_btor(working_dir, working_dir / (synth_filename.stem + ".btor"),
                                [synth_filename] + additional_sources, benchmark.design.top,
                                script_out=working_dir / "to_botr.sh")
        result = _run_synthesizer(working_dir, btor_filename, benchmark.testbench.table, opts)

        status = status_name_to_enum[result['status']]
        solutions = []
        if status == Status.Success:
            solutions = [s['assignment'] for s in result['solutions']]

        stats = SynthStats(solver_time_ns=result['solver-time'], past_k=result['past-k'], future_k=result['future-k'])

        return status, solutions, stats
