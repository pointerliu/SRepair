#!/usr/bin/env python3
# Copyright 2022-2024 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>
import multiprocessing
import signal
import math
import argparse
import copy
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import pyverilog.vparser.ast as vast
from benchmarks import Benchmark, load_project, get_benchmark
from benchmarks.result import create_buggy_and_original_diff, write_result
from rtlrepair import parse_verilog, serialize, do_repair, Synthesizer, preprocess, SynthOptions, Status
from rtlrepair.analysis import analyze_ast, AnalysisResults
from rtlrepair.synthesizer import SynthStats
from rtlrepair.templates import *
from rtlrepair.snn_templates import *
from rtlrepair.visitor import AstVisitor

_ToolName = "rtl-repair"

_bug_timeout = 10 * 60 # 10 min timeout for each bug.

_supported_solvers = {'z3', 'cvc4', 'yices2', 'boolector', 'bitwuzla', 'optimathsat', 'btormc'}
_available_templates = {
    'replace_literals': replace_literals,
    'assign_const': assign_const,
    'add_inversions': add_inversions,
    # 'replace_variables': replace_variables,
    'conditional_overwrite': conditional_overwrite,
    'add_guard': add_guard,
    'replace_cond_expr': replace_cond_expr,
    'add_cond_expr': add_cond_expr,

    'edge_flip': edge_flip,
    't0_type_voting': type_voting,
    't1_replace_atom': t1_replace_atom,
    't2_replace_cond': t2_replace_cond,
    't3_replace_assign': t3_replace_assign,
    't3_replace_assign_rr_t': t3_replace_assign_rr_t,
    't3_replace_assign_rr_synth': t3_replace_assign_rr_synth,
    't4_add_substitution': t4_add_substitution,
    't4_add_substitution_rr_synth': t4_add_substitution_rr_synth,
    't5_change_timing_assign': t5_change_timing_assign,
    't5_change_timing_subs_pre': t5_change_timing_subs_pre,
    't5_change_timing_subs_post': t5_change_timing_subs_post,
    't6_cond_overwrite_rr_t_pre': t6_cond_overwrite_rr_t_pre,
    't6_cond_overwrite_rr_t_post': t6_cond_overwrite_rr_t_post,
}
# _default_templates = ['replace_literals', 'assign_const', 'add_guard']
#  {'success': 17, 'cannot-repair': 10, 'no-repair': 1, 'timeout': 4}
# _default_templates = [
#     'replace_literals',
#     'add_guard',
#     'conditional_overwrite'
# ]


# _default_templates = ['t1_replace_atom', 'add_cond_expr', 'replace_cond_expr', ]
# {'success': 14, 'cannot-repair': 10, 'no-repair': 1, 'timeout': 7})

# _default_templates = ['t1_replace_atom', 't2_replace_cond','t3_replace_assign', 't4_add_substitution', ]
_default_templates = [
    't1_replace_atom',
    't2_replace_cond',
    't3_replace_assign',
    't4_add_substitution',
    't5_change_timing_assign',
    't5_change_timing_subs_pre',
    't5_change_timing_subs_post'
]


# _default_templates = ['t1_replace_atom']


# _default_templates = ['t1_replace_atom', 't2_replace_cond']
# _default_templates = ['t4_add_substitution']


@dataclass
class Options:
    show_ast: bool
    synth: SynthOptions
    templates: list
    skip_preprocessing: bool
    single_solution: bool = False  # restrict the number of solutions to one
    timeout: float = None  # set timeout after which rtl-repair terminates
    run_all_templates: bool = False
    per_template_timeout: float = None
    bound_arch: list = None


@dataclass
class Config:
    working_dir: Path
    benchmark: Benchmark
    opts: Options


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description='Repair Verilog file')
    parser.add_argument('--working-dir', dest='working_dir', help='Working directory, files might be overwritten!',
                        required=True)
    # benchmark selection
    parser.add_argument('--project', help='Project TOML file.', required=True)
    parser.add_argument('--bug', help='Name of the bug from the project TOML.', default=None)
    parser.add_argument('--testbench', help='Name of the testbench from the project TOML.', default=None)

    # options
    parser.add_argument('--solver', dest='solver', help='z3 or optimathsat', default="z3")
    parser.add_argument('--init', dest='init', help='how should states be initialized? [any], zero or random',
                        default="any")
    parser.add_argument('--show-ast', dest='show_ast', help='show the ast before applying any transformation',
                        action='store_true')
    parser.add_argument('--incremental', dest='incremental', help='use incremental solver',
                        action='store_true')
    parser.add_argument('--timeout', help='Max time to attempt a repair in seconds')
    available_template_names = ", ".join(_available_templates.keys())
    parser.add_argument('--templates', default=",".join(_default_templates),
                        help=f'Specify repair templates to use. ({available_template_names})')
    parser.add_argument('--skip-preprocessing', help='skip the preprocessing step', action='store_true')
    parser.add_argument('--verbose-synthesizer',
                        help='collect verbose output from the synthesizer which will be available in synth.txt',
                        action='store_true')
    parser.add_argument('--run-all-templates',
                        help='Instead of an early exit when a repair is found, this tries to run all templates available.',
                        action='store_true')
    parser.add_argument('--template-timeout', help='Applies a timeout to each individual template.')
    parser.add_argument('--past-k-step-size', help='Step size used in the incremental repair synthesizer.')
    parser.add_argument('--old-synthesizer', help='use the old synthesizer written in Scala',
                        action='store_true')
    parser.add_argument('--bound-arch', dest='bound_arch', default="",
                        help=f'Specify bounded architecture. e.g. 3,2,1')

    args = parser.parse_args()

    # benchmark selection
    project = load_project(Path(args.project))
    benchmark = get_benchmark(project, args.bug, testbench=args.testbench, use_trace_testbench=True)

    # options
    assert args.solver in _supported_solvers, f"unknown solver {args.solver}, try: {_supported_solvers}"
    assert args.init in {'any', 'zero', 'random'}
    synth_opts = SynthOptions(solver=args.solver, init=args.init, incremental=args.incremental,
                              verbose=args.verbose_synthesizer, past_k_step_size=args.past_k_step_size,
                              old_synthesizer=args.old_synthesizer)
    timeout = None if args.timeout is None else float(args.timeout)
    per_template_timeout = None if args.template_timeout is None else float(args.template_timeout)
    templates = []
    for t in args.templates.split(','):
        t = t.strip()
        assert t in _available_templates, f"Unknown template `{t}`. Try: {available_template_names}"
        templates.append(_available_templates[t])
    bound_arch = []
    for a in args.bound_arch.split(','):
        if len(a) == 0:
            continue
        bound_arch.append(int(a))
    opts = Options(show_ast=args.show_ast, synth=synth_opts, timeout=timeout, templates=templates,
                   skip_preprocessing=args.skip_preprocessing, run_all_templates=args.run_all_templates,
                   per_template_timeout=per_template_timeout,
                   bound_arch=bound_arch)

    return Config(Path(args.working_dir), benchmark, opts)


def create_working_dir(working_dir: Path):
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)


def find_solver_version(solver: str) -> str:
    arg = ["--version"]
    if solver == "btormc":
        arg += ["-h"]  # without this btormc does not terminate
    if solver == 'yices2':
        solver = 'yices-smt2'
    if solver == 'optimathsat':
        arg = ["-version"]
    r = subprocess.run([solver] + arg, check=True, stdout=subprocess.PIPE)
    return r.stdout.decode('utf-8').splitlines()[0].strip()


# return this if the synthesizer did not run or did not run properly (i.e. crashed)
NoSynthStat = SynthStats(solver_time_ns=0, past_k=-1, future_k=-1)

def enable_global_fix(template_name) -> bool:
    return template_name in ['t1_replace_atom', 't2_replace_cond', 't3_replace_assign'] or \
    template_name in ['replace_literals', 'add_guard', 'add_guard_no_cond', 'conditional_overwrite'] or \
    template_name in ['t3_replace_assign_rr_t', 't3_replace_assign_rr_synth', ]

def apply_template_at_node(ast, template, analysis, bound_arch=[]):
    def do_template(node):
        setattr(node, 'mark', 1)
        cpy_ast = copy.deepcopy(ast)
        ret = template(cpy_ast, copy.deepcopy(analysis), bound_arch)
        setattr(node, 'mark', None)
        return ret, cpy_ast

    class TemplateVisitor(AstVisitor):
        def __init__(self):
            super().__init__(only_first_module=True)
            self.rets = []

            self._in_gen_blk = False

            t_name = template.__name__
            self.en_cond = False
            self.en_assign = False
            self.en_subs = False
            self.en_blk_subs = False
            self.en_always = False

            self.en_atom = False
            if 't5_change_timing_assign' in t_name:
                self.en_assign = True
                self.en_blk_subs = True
            if 't5_change_timing_subs' in t_name:
                self.en_subs = True
            if 't1' in t_name:
                self.en_atom = True
            if 't2' in t_name:
                self.en_cond = True
            if 't3' in t_name:
                self.en_assign = True
            if 't4' in t_name:
                self.en_subs = True
                self.en_blk_subs = True
            if 't6' in t_name:
                self.en_always = True

        def visit(self, node):
            if isinstance(node, vast.ModuleDef):
                if self.visited_first_module and self.only_first_module:
                    return node  # done
                self.visited_first_module = True
            method = 'visit_' + node.__class__.__name__

            visitor = getattr(self, method, self.generic_visit)
            ret = visitor(node)
            if ret is None:
                return node
            return ret

        def visit_GenerateStatement(self, node: vast.GenerateStatement):
            self._in_gen_blk = True
            for s in node.items:
                self.visit(s)
            self._in_gen_blk = False
            return node

        def visit_Always(self, node: vast.Always):
            if not self.en_always:
                return self.generic_visit(node)
            ret, cpy_ast = do_template(node)
            self.rets.append((ret, cpy_ast))

            return node

        def visit_Assign(self, node: vast.Assign):
            if not self.en_assign:
                return self.generic_visit(node)

            # consider generate
            # if self._in_gen_blk:
            #     return node
            ret, cpy_ast = do_template(node)
            self.rets.append((ret, cpy_ast))

            return node

        def visit_IfStatement(self, node: vast.IfStatement):
            if self.en_cond:
                ret, cpy_ast = do_template(node.cond)
                self.rets.append((ret, cpy_ast))

            self.visit(node.cond)
            self.visit(node.true_statement)
            self.visit(node.false_statement)
            return node

        # def visit_Block(self, node: vast.Block):
        #     ret, cpy_ast = do_template(node)
        #     self.rets.append((ret, cpy_ast))
        #     for stmt in node.statements:
        #         self.visit(stmt)
        #     return node
        #
        # def visit_CaseStatement(self, node: vast.CaseStatement):
        #     ret, cpy_ast = do_template(node)
        #     self.rets.append((ret, cpy_ast))
        #     return node

        def visit_NonblockingSubstitution(self, node: vast.NonblockingSubstitution):
            if not self.en_subs:
                return self.generic_visit(node)
            ret, cpy_ast = do_template(node)
            self.rets.append((ret, cpy_ast))

            return node

        def visit_BlockingSubstitution(self, node: vast.BlockingSubstitution):
            if not self.en_blk_subs:
                return self.generic_visit(node)
            ret, cpy_ast = do_template(node)
            self.rets.append((ret, cpy_ast))

            return node

        def visit_IntConst(self, node: vast.IntConst):
            if not self.en_atom:
                return self.generic_visit(node)
            ret, cpy_ast = do_template(node)
            self.rets.append((ret, cpy_ast))
            return node

        def visit_Identifier(self, node: vast.Identifier):
            if not self.en_atom:
                return self.generic_visit(node)
            ret, cpy_ast = do_template(node)
            self.rets.append((ret, cpy_ast))
            return node

        def visit_Decl(self, node: vast.Decl):
            if not self.en_atom:
                return self.generic_visit(node)
            ret, cpy_ast = do_template(node)
            self.rets.append((ret, cpy_ast))
            return node

    rets = []
    if enable_global_fix(template.__name__):
        # 't6_cond_overwrite_rr_t_pre', 't6_cond_overwrite_rr_t_post']:
        cpy_ast = copy.deepcopy(ast)
        ret = template(cpy_ast, copy.deepcopy(analysis), True, bound_arch)
        rets.append((ret, cpy_ast))
    else:
        cu = TemplateVisitor()
        cu.visit(ast)
        rets = cu.rets

    return rets


def try_template(config: Config, ast, prefix: str, template, statistics: dict, analysis: AnalysisResults,
                 solution_count: int,
                 preprocess_change_count: int) -> (
        Status, list):
    # if config.opts.per_template_timeout is not None:
    #     signal.alarm(int(math.ceil(config.opts.per_template_timeout)))

    start_time = time.monotonic()
    # create a directory for this particular template
    template_name = template.__name__
    template_dir = config.working_dir / (prefix + template_name)
    if template_dir.exists():
        shutil.rmtree(template_dir)
    os.mkdir(template_dir)

    # apply template any try to synthesize a solution

    status_glb = Status.CannotRepair
    solutions = []
    copied_ast = copy.deepcopy(ast)
    for pos, (blockified, ast) in enumerate(
            apply_template_at_node(copied_ast, template, analysis, config.opts.bound_arch)):

        # timeout at one anchor, only for not global templates
        tm = math.ceil(config.opts.timeout if config.opts.timeout is not None else config.opts.per_template_timeout)
        if config.opts.timeout or config.opts.per_template_timeout:
            if not enable_global_fix(template_name):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(tm))

        # try to find a change that fixes the design
        synth_start_time = time.monotonic()
        synth = Synthesizer()
        synth_crash = False
        try:
            status, assignments, synth_stats = synth.run(template_dir, config.opts.synth, ast, config.benchmark)
        except TimeoutError as e:
            # is this error for us?
            # status, assignments, synth_stats = Status.Timeout, [], NoSynthStat
            continue
        except subprocess.TimeoutExpired as e:
            continue
            # if config.opts.per_template_timeout is not None:
            #     status, assignments, synth_stats = Status.Timeout, [], NoSynthStat
            # else:
            #     assert config.opts.timeout is not None  # global timeout instead!
            #     raise e  # dispatch to top
        except subprocess.CalledProcessError as e:
            if 'Found topological loop' in str(e.stderr):
                print('Found topological loop')
                status, assignments, synth_stats = Status.CannotRepair, [], NoSynthStat
            else:
                # something crashed, so we cannot repair this bug
                status, assignments, synth_stats = Status.CannotRepair, [], NoSynthStat
                synth_crash = True
        finally:
            signal.alarm(0)
            # signal.signal(signal.SIGALRM, signal.SIG_DFL)

        if synth_crash:
            print("synth crashed")
            status_glb = Status.Crash
            break

        synth_time = time.monotonic() - synth_start_time
        template_time = time.monotonic() - start_time
        solver_time = synth_stats.solver_time_ns / 1000.0 / 1000.0 / 1000.0

        if status == Status.Success:
            status_glb = status
            # pick first solution if only one was requested
            if config.opts.single_solution:
                assignments = assignments[:1]
            for ii, assignment in enumerate(assignments):
                # execute synthesized repair
                changes = do_repair(ast, assignment, blockified)
                tmp_prefix = f"{config.benchmark.bug.buggy.stem}.repaired.{prefix}.{ii + solution_count}.{pos}"
                with open(template_dir / f"{tmp_prefix}.changes.txt", "w") as f:
                    f.write(f"{template_name}\n")
                    f.write(f"{len(changes)}\n")
                    f.write('\n'.join(f"{line}: {a} -> {b}" for line, a, b in changes))
                    f.write('\n')
                repaired_filename = config.working_dir / f"{tmp_prefix}.v"
                with open(repaired_filename, "w") as f:
                    f.write(serialize(ast))
                # meta info for the solution
                meta = {'changes': len(changes), 'template': template_name, 'synth_time': synth_time,
                        'template_time': template_time,
                        'solver_time': solver_time,
                        'past_k': synth_stats.past_k, 'future_k': synth_stats.future_k,
                        }
                solutions.append((repaired_filename, meta))

        if status == Status.NoRepair and preprocess_change_count > 0:
            solutions = [(
                config.working_dir / f"{config.benchmark.bug.buggy.stem}.repaired.v",
                {'template': "preprocess", 'changes': preprocess_change_count})
            ]
            status_glb = Status.Success
        elif status == Status.NoRepair:
            status_glb = Status.NoRepair

        statistics[template_name] = {
            'prefix': prefix, 'solver_time': solver_time,
            'status': status_glb.name, 'synth_time': synth_time, 'template_time': template_time,
            'solutions': len(solutions)
        }

        if status_glb == Status.Success or status_glb == Status.NoRepair:
            break

    return status_glb, solutions


def try_templates_in_sequence(config: Config, ast, statistics: dict, preprocess_change_count, ret_queue) -> (Status, list, dict):
    all_solutions = []
    # instantiate repair templates, one after another
    # note: when  we tried to combine replace_literals and add_inversion, tests started taking a long time
    for ii, template in enumerate(config.opts.templates):
        prefix = f"{ii + 1}_"
        # we need to deep copy the ast since the template is going to modify it in place!
        ast_copy = copy.deepcopy(ast)
        analysis = analyze_ast(ast_copy)

        try:
            status, solutions = try_template(config, ast_copy, prefix, template, statistics, analysis,
                                             len(all_solutions),
                                             preprocess_change_count)
            if status == Status.Crash:
                ret_queue.put((status, all_solutions))
                return status, all_solutions
        except TimeoutError as e:
            status, solutions = Status.Timeout, []
            print(f'{template.__name__} timeout.')
            continue

        # early exit if there is nothing to do or if we found a solution and aren't instructed to run all templates
        if config.opts.run_all_templates:
            all_solutions += solutions
            # ast = ast_copy
            continue
        if status == Status.NoRepair or (not config.opts.run_all_templates and status == Status.Success):
            if status == Status.Success:
                # keep going if the current solution is pretty large
                # min_changes = min(s[1]['changes'] for s in solutions)
                # if min_changes <= 3:
                ret_queue.put((status, solutions))
                return status, solutions
                # else:
                #     all_solutions += solutions
            else:
                ret_queue.put((status, solutions))
                return status, solutions
        else:
            all_solutions += solutions
        # ast = ast_copy

    # status = Status.Success if len(all_solutions) != 0 else Status.CannotRepair
    if len(all_solutions) != 0:
        status = Status.Success
    ret_queue.put((status, all_solutions))
    return status, all_solutions


def repair(config: Config, statistics: dict):
    preprocess_start_time = time.monotonic()
    if config.opts.skip_preprocessing:
        filename, preprocess_change_count = config.benchmark.bug.buggy, 0
    else:
        # preprocess the input file to fix some obvious problems that violate coding styles and basic lint rules
        filename, preprocess_change_count = preprocess(config.working_dir, config.benchmark)
    statistics['preprocess'] = {'time': time.monotonic() - preprocess_start_time, 'changes': preprocess_change_count}

    ast = parse_verilog(filename, config.benchmark.design.directory)
    if config.opts.show_ast:
        ast.show()

    # status, solutions = try_templates_in_sequence(config, ast, statistics, preprocess_change_count)

    ret_queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=try_templates_in_sequence, args=(config, ast, statistics, preprocess_change_count, ret_queue))
    process.start()

    # set timeout for per bug
    process.join(timeout=_bug_timeout)

    if process.is_alive():
        status, solutions = Status.Timeout, []
        process.terminate()
        process.join()
    else:
        status, solutions = ret_queue.get()

    # create repaired file in the case where the synthesizer had to make no changes
    if status == Status.NoRepair:
        # make sure we copy over the repaired file
        repaired_dst = config.working_dir / f"{config.benchmark.bug.buggy.stem}.repaired.v"
        shutil.copy(src=filename, dst=repaired_dst)
        # if the preprocessor made a change and that resulted in not needing any change to fix the benchmark
        # then we successfully repaired the design with the preprocessor
        if preprocess_change_count > 0:
            solutions = [(repaired_dst, {'template': "preprocess", 'changes': preprocess_change_count})]
            status = Status.Success
        # otherwise the circuit was already correct
        else:
            solutions = [(repaired_dst, {'template': "", 'changes': 0})]

    return status, solutions


def timeout_handler(signum, frame):
    print("timeout")
    raise TimeoutError()


def check_verilator_version(opts: Options):
    """ Makes sure that the major version of verilator is 4 if we are using preprocessing.
        This is important because verilator 5 has significant changes to what it reports as warnings in lint mode.
    """
    if opts.skip_preprocessing: return
    version_out = subprocess.run(["verilator", "-version"], stdout=subprocess.PIPE).stdout
    version = version_out.split()[1]
    major_version = int(version.split(b'.')[0])
    assert major_version == 4, f"Unsupported verilator version {version} detected. " \
                               f"Please provide Verilator 4 on your path instead!"


def main():
    config = parse_args()
    assert not (config.opts.timeout and config.opts.per_template_timeout), \
        "timeout and template-timeout options are not compatible!"

    check_verilator_version(config.opts)
    create_working_dir(config.working_dir)

    # if config.opts.timeout:
    #     signal.alarm(int(math.ceil(config.opts.timeout)) * len(_default_templates))
    # signal.alarm(int(math.ceil(config.opts.timeout)))

    # create benchmark description to make results self-contained
    create_buggy_and_original_diff(config.working_dir, config.benchmark)

    # run repair
    statistics = {}
    start_time = time.monotonic()
    try:
        status, solutions = repair(config, statistics)
    except TimeoutError:
        status, solutions = Status.Timeout, []
    delta_time = time.monotonic() - start_time
    statistics['total_time'] = delta_time

    # save results to disk
    success = status in {Status.Success, Status.NoRepair}
    write_result(config.working_dir, config.benchmark, success,
                 repaired=solutions, seconds=delta_time, tool_name=_ToolName,
                 custom={'status': status.value, 'statistics': statistics})


if __name__ == '__main__':
    main()
