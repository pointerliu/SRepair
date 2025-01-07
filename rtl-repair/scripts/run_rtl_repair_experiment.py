#!/usr/bin/env python3
# Copyright 2022-2023 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>
from collections import defaultdict

import tomli
import sys
import os
import shutil
import argparse
from pathlib import Path
from dataclasses import dataclass
import subprocess

# add root dir in order to be able to load "benchmarks" module
_script_dir = Path(__file__).parent.resolve()
_root_dir = _script_dir.parent
sys.path.append(str(_root_dir))
import benchmarks
from benchmarks import Benchmark, assert_file_exists

# global experiment default settings
_solver = 'bitwuzla'
_incremental = True
_init = 'random'
# _timeout = 300  # 5 minute timeout, but 5 min for SRepair on cirfix and fpga is too slow
_timeout = 120  # 5 minute timeout, but 5 min for SRepair on cirfix and fpga is too slow
                # Note that, this timeout is set for each fix anchor
_verbose_synth = True

# the FPGA benchmarks all have testbenches from Verilator which assume a zero init
_init_fpga = 'zero'
# the FPGA benchmarks benefit from running with yices2
_solver_fpga = 'bitwuzla'
# _bound_arch = '3,2,1'
_bound_arch = ''


@dataclass
class ExpConfig:
    incremental: bool
    timeout: int  # per template timeout when all_templates is true
    all_templates: bool
    past_k_step_size: int = None
    fpga_instead_of_cirfix_bench: bool = False


@dataclass
class Config:
    working_dir: Path
    skip_existing: bool
    skip_preprocess: bool
    experiment: str
    tag: str


# possible experiments:
ExpDefault = 'default'
ExpAllTemplates = 'all-templates'
ExpBasicSynth = 'basic-synth'
ExpPastKOne = 'past-k-1'
ExpFpga = 'fpga'
ExpFpgaAll = 'fpga-all'
Configs: dict[str, ExpConfig] = {
    ExpDefault: ExpConfig(incremental=True, timeout=_timeout, all_templates=False),
    ExpAllTemplates: ExpConfig(incremental=True, timeout=_timeout, all_templates=True),
    ExpBasicSynth: ExpConfig(incremental=False, timeout=_timeout, all_templates=False),
    ExpPastKOne: ExpConfig(incremental=True, timeout=_timeout, all_templates=False, past_k_step_size=1),
    ExpFpga: ExpConfig(incremental=True, timeout=_timeout, all_templates=False, fpga_instead_of_cirfix_bench=True),
    ExpFpgaAll: ExpConfig(incremental=True, timeout=_timeout, all_templates=True, fpga_instead_of_cirfix_bench=True),
}
Exps = list(Configs.keys())


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description='run repairs')
    parser.add_argument("--working-dir", dest="working_dir", required=True)
    parser.add_argument("--skip-existing", dest="skip", action="store_true", default=False)
    parser.add_argument("--skip-preprocess", dest="skip_preprocess", action="store_true", default=False)
    parser.add_argument("--clear", dest="clear", help="clear working dir", action="store_true", default=False)
    parser.add_argument("--experiment", help=f'Pick one of: {Exps}', default=ExpDefault)
    parser.add_argument("--tag", help=f'Approach Name', default="RR")
    args = parser.parse_args()

    assert args.experiment in Exps, f"Invalid experiment {args.experiment}, pick one of: {Exps}"

    # parse and create working dir
    working_dir = Path(args.working_dir)
    parent_dir = working_dir.parent
    assert parent_dir.exists(), f"{parent_dir} does not exist"
    assert parent_dir.is_dir(), f"{parent_dir} is not a directory"
    if args.clear and working_dir.exists():
        shutil.rmtree(working_dir)
    if not working_dir.exists():
        os.mkdir(working_dir)

    return Config(working_dir, args.skip, args.skip_preprocess, args.experiment, tag=args.tag)


def run_rtl_repair(working_dir: Path, benchmark: Benchmark, project_toml: Path, bug: str, testbench: str, solver, init,
                   incremental, timeout=None, skip_preprocess=False, all_templates: bool = False,
                   past_k_step_size: int = None,
                   templates=None):
    # determine the directory name from project and bug name
    if templates is None:
        templates = []
    out_dir = working_dir / benchmark.name
    args = [
        "--project", str(project_toml.resolve()),
        "--solver", solver,
        "--working-dir", str(out_dir.resolve()),
        "--init", init,
    ]
    if bug:  # bug is optional to allow for sanity-check "repairs" of the original design
        args += ["--bug", bug]
    if testbench:
        args += ["--testbench", testbench]
    if incremental:
        args += ["--incremental"]
        if past_k_step_size:
            args += ["--past-k-step-size", str(past_k_step_size)]
    if all_templates:
        args += ["--run-all-templates"]
        if timeout is not None:
            args += [f"--template-timeout", str(timeout)]
    elif timeout is not None:
        args += [f"--timeout", str(timeout)]
    if _verbose_synth:
        args += ["--verbose-synthesizer"]
    if skip_preprocess:
        args += ["--skip-preprocessing"]
    if len(_bound_arch) != 0:
        args += ["--bound-arch", _bound_arch]
    if len(templates) != 0:
        args += ["--templates", ','.join(templates)]

    rtl_repair = _root_dir / "rtlrepair.py"
    assert_file_exists("RTL-Repair script", rtl_repair)
    cmd = [str(rtl_repair.resolve())] + args
    # for debugging:
    cmd_str = ' '.join(cmd)
    print(f"\n{cmd_str}")
    # run from working directory, this is necessary because PyVerilog creates some
    # temporary files that might otherwise conflict with other experiments that are
    # run in parallel
    cwd = working_dir

    try:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, check=True, cwd=cwd)
    except subprocess.CalledProcessError as r:
        print(f"Failed to execute command: {cmd_str}")
        return 'failed', 0, None

    with open(out_dir / "result.toml", 'rb') as ff:
        dd = tomli.load(ff)
    status = dd['custom']['status']
    if dd['result']['success']:
        repairs = dd['repairs']
        template = repairs[0]['template']
        changes = repairs[0]['changes']
    else:
        changes = 0
        template = None

    return status, changes, template


def run_all_cirfix_benchmarks(conf: Config, projects: dict) -> dict:
    statistics = defaultdict(int)
    exp_conf = Configs[conf.experiment]
    for name, project in projects.items():
        # if name != 'zipcpu-spi-c1-c3-d9':
        #     print(name)
        #     continue
        # overwrite for manual adjustments that we had to make
        if name in benchmarks.rtlrepair_replacements:
            project_toml = benchmarks.rtlrepair_replacements[name]
            project = benchmarks.load_project(project_toml)
        else:
            project_toml = benchmarks.projects[name]
        bbs = benchmarks.get_benchmarks(project)
        for bb in bbs:
            # if bb.bug.name != 'c3':
            #     continue

            assert isinstance(bb, Benchmark)
            # skip irrelevant benchmarks
            if exp_conf.fpga_instead_of_cirfix_bench:
                if not benchmarks.is_fpga_debugging_benchmark(bb):
                    continue
            else:
                if not benchmarks.is_cirfix_paper_benchmark(bb):
                    continue
            testbench = benchmarks.pick_trace_testbench(project, bug=bb.bug.name)
            sys.stdout.write(f"{bb.name} w/ {testbench.name}")
            sys.stdout.flush()
            if exp_conf.fpga_instead_of_cirfix_bench:
                init = _init_fpga
                solver = _solver_fpga
            else:
                init = _init
                solver = _solver

            templates = []

            if conf.tag == 'RR':
                templates.extend([
                    'replace_literals',
                    'conditional_overwrite',
                    'add_guard'
                ])
            elif conf.tag == 'SNN':
                templates.extend([
                    't1_replace_atom',
                    't2_replace_cond',
                    't3_replace_assign',
                    't4_add_substitution',
                    't5_change_timing_assign',
                    't5_change_timing_subs_pre',
                    't5_change_timing_subs_post'
                ])
            else:
                raise Exception(f"Unknown approach name {conf.tag}")

            status, changes, template = run_rtl_repair(conf.working_dir, bb, project_toml, bb.bug.name,
                                                       testbench=testbench.name, solver=solver, init=init,
                                                       incremental=exp_conf.incremental,
                                                       timeout=exp_conf.timeout,
                                                       skip_preprocess=conf.skip_preprocess,
                                                       all_templates=exp_conf.all_templates,
                                                       past_k_step_size=exp_conf.past_k_step_size,
                                                       templates=templates)
            print(f" --> {status}")
            statistics[status] += 1

    return statistics


def main():
    conf = parse_args()
    projects = benchmarks.load_all_projects()
    statistics = run_all_cirfix_benchmarks(conf, projects)
    print(statistics)


if __name__ == '__main__':
    main()
