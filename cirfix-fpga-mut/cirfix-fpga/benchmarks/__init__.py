# Copyright 2022-2023 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>
# benchmark python library
import os.path
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List

import tomli

benchmark_dir = Path(__file__).parent.resolve()
_cirfix_benchmark_dir = benchmark_dir / "cirfix"
_fpga_benchmark_dir = benchmark_dir / "fpga-debugging"
_opencores_dir = _cirfix_benchmark_dir / "opencores"
_sha3_dir = _opencores_dir / "sha3" / "low_throughput_core"

# _hardware_bugbase = Path('/home/lzz/hAPR/asplos22-hardware-debugging-artifact/')
_hardware_bugbase = Path('/home/lzz/hAPR/asplos22-hardware-debugging-artifact/') \
    if os.environ.get('HARDWARE_BUGBASE') is None else Path(os.environ.get('HARDWARE_BUGBASE'))

_fpga_dir = _hardware_bugbase / 'hardware-bugbase-own'
_a4v_dir = benchmark_dir / 'Assignment4V'
_hw_cwes_dir = benchmark_dir / 'HW_CWEs-cirfix'

projects = {
    "decoder_3_to_8": _cirfix_benchmark_dir / "decoder_3_to_8",
    "first_counter_overflow": _cirfix_benchmark_dir / "first_counter_overflow",
    "flip_flop": _cirfix_benchmark_dir / "flip_flop",
    "fsm_full": _cirfix_benchmark_dir / "fsm_full",
    "lshift_reg": _cirfix_benchmark_dir / "lshift_reg",
    "mux_4_1": _cirfix_benchmark_dir / "mux_4_1",
    "sdram_controller": _cirfix_benchmark_dir / "sdram_controller",
    "i2c_master": _opencores_dir / "i2c" / "master.toml",
    "i2c_slave": _opencores_dir / "i2c" / "slave.toml",
    "pairing": _opencores_dir / "pairing",
    "reed_solomon_decoder": _opencores_dir / "reed_solomon_decoder",
    "sha3_f_permutation": _sha3_dir / "f_permutation.toml",
    "sha3_keccak": _sha3_dir / "keccak.toml",
    "sha3_padder": _sha3_dir / "padder.toml",
    "axi-lite-s1": _fpga_benchmark_dir / "axi-lite-s1",
    "axi-stream-s2": _fpga_benchmark_dir / "axi-stream-s2",
    "axis-adapter-s3": _fpga_benchmark_dir / "axis-adapter-s3",
    "axis-async-fifo-c4": _fpga_benchmark_dir / "axis-async-fifo-c4",
    "axis-fifo-d4": _fpga_benchmark_dir / "axis-fifo-d4",
    "axis-fifo-d12": _fpga_benchmark_dir / "axis-fifo-d12",
    "axis-frame-fifo-d11": _fpga_benchmark_dir / "axis-frame-fifo-d11",
    "axis-frame-len-d13": _fpga_benchmark_dir / "axis-frame-len-d13",
    "axis-switch-d8": _fpga_benchmark_dir / "axis-switch-d8",
    # skipping fadd since it employs advanced system Verilog constructs
    "zipcpu-spi-c1-c3-d9": _fpga_benchmark_dir / "zipcpu-spi-c1-c3-d9",
}

fpga_projects = ["axi-lite-s1", "axi-stream-s2", "axis-adapter-s3", "axis-async-fifo-c4", "axis-fifo-d4",
                 "axis-fifo-d12", "axis-frame-fifo-d11", "axis-frame-len-d13", "axis-switch-d8", "zipcpu-spi-c1-c3-d9"]

cirfix_seeds = {
    "decoder_3_to_8": {
        "wadden_buggy1": "repair_2021-07-16-11:18:47",  # should take around 13984.3s
        "wadden_buggy2": None,  # was not repaired
    },
    "first_counter_overflow": {
        "wadden_buggy1":  "repair_2020-09-23-11:24:14",  # should take around 19.8s
        "wadden_buggy2":  "repair_2020-10-23-11:15:58",  # should take around 27781.3s
        "kgoliya_buggy1": "repair_2020-09-23-11:26:48",  # should take around 32239.2s
    },
    "flip_flop": {
        "wadden_buggy1": "repair_2020-09-22-16:19:54",   # should take around 7.8s
        "wadden_buggy2": "repair_2020-09-22-16:20:32",   # should take around 923.5s
    },
    "fsm_full": {
        "wadden_buggy1":   None,                          # was not repaired
        "wadden_buggy2":   "repair_2020-09-22-16:43:18",  # should take around 1536.4s
        "ssscrazy_buggy1": "repair_2020-09-22-17:11:14",  # should take around 37.03s
        "ssscrazy_buggy2": "repair_2020-09-22-17:13:29",  # should take around 4282.2s
    },
    "lshift_reg": {
        "wadden_buggy1":  "repair_2020-09-22-16:13:12",  # should take around 14.6s
        "wadden_buggy2":  "repair_2020-09-22-16:16:14",  # should take around 33.74s
        "kgoliya_buggy1": "repair_2020-09-22-16:01:26",  # should take around 7.8s
    },
    "mux_4_1": {
        "wadden_buggy1":  "repair_2021-07-20-23:50:05",  # should take around 15387.87s
        "wadden_buggy2":  "repair_2021-07-21-07:22:28",  # should take around 10315.4s
        "kgoliya_buggy1": None,                          # was not repaired
    },
    "i2c_slave": {
        "wadden_buggy1": "repair_2020-09-24-09:43:26",   # should take around 183s
        "wadden_buggy2": "repair_2020-09-24-09:39:10",   # should take around 57.9s
    },
    "i2c_master": {
        "kgoliya_buggy1": "repair_2020-10-14-11:25:36",  # should take around 1560.61s
    },
    "sha3_keccak": {
        "wadden_buggy1": "repair_2020-09-24-09:48:40",   # should take around 50.4s
        "wadden_buggy2": None,                           # was not repaired
        "round_ssscrazy_buggy1": None,                   # was not repaired
    },
    "sha3_padder": {
        "ssscrazy_buggy1": "repair_2020-09-24-15:16:49",   # should take around 50s
    },
    "pairing": {
        "wadden_buggy1":  None,   # was not repaired
        "wadden_buggy2":  None,   # was not repaired
        "kgoliya_buggy1": None,   # was not repaired
    },
    "reed_solomon_decoder": {
        "BM_lamda_ssscrazy_buggy1": None,  # was not repaired
        "out_stage_ssscrazy_buggy1": "repair_2020-09-29-23:31:29",  # should take around 28547.81s
    },
    "sdram_controller": {
        "wadden_buggy1":  "repair_2020-09-30-23:15:14",  # should take around 16607.6s
        "wadden_buggy2":  None,   # was not repaired
        "kgoliya_buggy2": None,   # was not repaired
    },
}

rtlrepair_replacements = {
    # We had to remove the tri-state buses by replacing them with several digital signals in order to work around
    # limitations in yosys which we use to lower the circuit into a transition system description.
    # Replacing tri-state signals _could_ be automated with a yosys are pyverilog based compiler pass, but
    # we did not deem that necessary for our research prototype.
    "sdram_controller": _cirfix_benchmark_dir / "sdram_controller" / "no_tri_state.toml",
    # We had to switch the asynchronous reset to a synchronous one to make our repair implementation work
    # because for asynchronous resets, the reset value has to be a constant
    # There are two ways to solve this issue:
    # 1) Change yosys to allow for non-constant async reset values as this is only important for synthesis, not
    #    for formal
    # 2) Transform the Verilog before giving it to yosys to simulate an async reset with a sync reset,
    #    similar to what the built-in yosys async2sync pass does anyway. We would just need to do it before Yosys
    #    in order to pass the async value must be const check.
    "i2c_master": _opencores_dir / "i2c" / "master_sync_reset.toml",
}


# see table 3 in the cirfix paper
# (description, cat, repair time, status)
Correct = 'correct'
Plausible = 'plausible'
Timeout = 'timeout'
benchmark_to_cirfix_paper_table_3 = {
    "decoder_3_to_8": {
        "wadden_buggy1": ("Two separate numeric errors", 1, 13984.3, Correct),
        "wadden_buggy2": ("Incorrect assignment", 2, None, Timeout),
    },
    "first_counter_overflow": {
        "wadden_buggy1":  ("Incorrect sensitivity list", 1, 19.8, Correct),
        "kgoliya_buggy1":  ("Incorrect reset", 1, 32239.2, Correct),
        "wadden_buggy2": ("Incorrect incremental of counter", 1, 27781.3, Correct)
    },
    "flip_flop": {
        "wadden_buggy1": ("Incorrect conditional", 1, 7.8, Correct),
        "wadden_buggy2": ("Branches of if-statement swapped", 1, 923.5, Correct),
    },
    "fsm_full": {
        "wadden_buggy1":   ("Incorrect case statement", 1, None, Timeout),
        "ssscrazy_buggy2":   ("Incorrectly blocking assignments", 1, 4282.2, Plausible),
        "wadden_buggy2": ("Assignment to next state and default in case statement omitted", 2, 1536.4, Plausible),
        "ssscrazy_buggy1": ("Assignment to next state omitted, incorrect sensitivity list", 2, 37.0, Correct),
    },
    "lshift_reg": {
        "wadden_buggy1":  ("Incorrect blocking assignment", 1, 14.6, Correct),
        "wadden_buggy2":  ("Incorrect conditional", 1, 33.74, Correct),
        "kgoliya_buggy1": ("Incorrect sensitivity list", 1, 7.8, Correct),
    },
    "mux_4_1": {
        "kgoliya_buggy1":  ("1 bit instead of 4 bit output", 1, None, Timeout),
        "wadden_buggy2":  ("Hex instead of binary constants", 1, 10315.4, Plausible),
        "wadden_buggy1": ("Three separate numeric errors", 2, 15387.9, Plausible),
    },
    "i2c_slave": {
        "wadden_buggy1": ("Incorrect sensitivity list", 2, 183.0, Correct),
        "wadden_buggy2": ("Incorrect address assignment", 2, 57.9, Plausible),
    },
    "i2c_master": {
        "kgoliya_buggy1": ("No command acknowledgement", 2, 1560.5, Correct),
    },
    "sha3_keccak": {
        "wadden_buggy1": ("Off-by-one error in loop", 1, 50.4, Correct),
        "round_ssscrazy_buggy1": ("Incorrect bitwise negation", 1, None, Timeout),
        "wadden_buggy2": ("Incorrect assignment to wires", 2, None, Timeout),
    },
    "sha3_padder": {
        "ssscrazy_buggy1": ("Skipped buffer overflow check", 2, 50.0, Correct),
    },
    "pairing": {
        "wadden_buggy1":  ("Incorrect logic for bitshifting", 1, None , Timeout),
        "kgoliya_buggy1":  ("Incorrect operator for bitshifting", 1, None, Timeout),
        "wadden_buggy2": ("Incorrect instantiation of modules", 1, None, Timeout),
    },
    "reed_solomon_decoder": {
        "BM_lamda_ssscrazy_buggy1": ("Insufficient register size for decimal values", 1, None, Timeout),
        "out_stage_ssscrazy_buggy1": ("Incorrect sensitivity list for reset", 2, 28547.8, Correct),
    },
    "sdram_controller": {
        "wadden_buggy2":  ("Numeric error in definitions", 1, None, Timeout),
        "kgoliya_buggy2":  ("Incorrect case statement", 2, None, Timeout),
        "wadden_buggy1": ("Incorrect assignments to registers during synchronous reset", 2, 16607.6, Correct),
    },
}

@dataclass
class Bug:
    name: str
    original: Path
    buggy: Path

@dataclass
class Testbench:
    name: str
    bugs: list[str] # optional list of bugs that are revealed by this particular tb
    tags: list[str]


@dataclass
class VerilogOracleTestbench(Testbench):
    """ The style of testbench used by CirFix """
    sources: list[Path]
    output: str
    oracle: Path
    timeout: float = None
    init_files: list[Path] = field(default_factory=list)


@dataclass
class TraceTestbench(Testbench):
    """ For RTL-Repair we use I/O traces that were pre-recorded from the Verilog testbench """
    table: Path

@dataclass
class Design:
    top: str
    directory: Path
    sources: list[Path]

@dataclass
class Project:
    name: str
    design: Design
    bugs: list[Bug]
    testbenches: list[Testbench]


@dataclass
class Benchmark:
    project_name: str
    design: Design
    bug: Bug
    testbench: Testbench
    @property
    def name(self):
        return f"{self.project_name}_{self.bug.name}_{self.testbench.name}"


def parse_path(path: str, base: Path = Path("."), must_exist: bool = False) -> Path:
    if os.path.isabs(path):
        path = Path(path)
    else:
        path = base / path
    if must_exist:
        assert path.exists(), f"{path} does not exist!"
    return path


def _load_bug(base_dir: Path, dd: dict) -> Bug:
    original = None
    if 'original' in dd and len(dd['original']) > 0:
        original = parse_path(dd['original'], base_dir, True)
    return Bug(
        name=dd['name'],
        original=original,
        buggy=parse_path(dd['buggy'], base_dir, True),
    )


def _load_testbench(base_dir: Path, dd: dict) -> Testbench:
    # common to both kinds of testbenches
    name = dd['name']
    tags = dd['tags'] if 'tags' in dd else []
    bugs = dd['bugs'] if 'bugs' in dd else None
    if 'oracle' in dd:
        inits = [] if 'init-files' not in dd else [parse_path(pp, base_dir, True) for pp in dd['init-files']]
        tt = VerilogOracleTestbench(
            name=name, tags=tags, bugs=bugs,
            sources=[parse_path(pp, base_dir, True) for pp in dd['sources']],
            output=dd['output'],
            oracle=parse_path(dd['oracle'], base_dir, True),
            init_files=inits,
        )
        if "timeout" in dd:
            tt.timeout = float(dd["timeout"])
    else:
        tt = TraceTestbench(name=name, tags=tags, bugs=bugs, table=parse_path(dd['table'], base_dir, True))
    return tt


def _load_list(project_dir: Path, dd: dict, name: str, load_foo) -> list:
    if name not in dd:
        return []
    return [load_foo(project_dir, ee) for ee in dd[name]]

def find_project_name_and_toml(filename: Path, is_mut: bool = False) -> (str, Path):
    """ auto discovers the concrete path to the project toml and the project name """
    # if a directory is provided, we try to open to project.toml
    if filename.is_dir():  # <-- this is the good case: the project specifies what it wants to be called
        name = filename.name
        filename = filename / ("project.toml" if not is_mut else "project_mut.toml")
    else:  # <-- ugly, hacky heuristics to get a "good" project name base on the filepath
        name = filename.stem
        # if we are given a path to a file name `project.toml` we assume that the directory is the project name
        if name == "project":
            name = filename.parent.name
    return name, filename


def load_project(filename: Path, is_mut: bool = False) -> Project:
    name, filename = find_project_name_and_toml(filename, is_mut)
    with open(filename, 'rb') as ff:
        dd = tomli.load(ff)
    assert 'project' in dd, f"{filename}: no project entry"
    project = dd['project']
    if 'name' in project:
        name = project['name']
    top = project['toplevel'] if 'toplevel' in project else None
    base_dir = filename.parent
    project_dir = parse_path(project['directory'], base_dir, must_exist=True)
    bugs = _load_list(base_dir, dd, "bugs", _load_bug)
    bugs = [bid for bid in bugs if (is_mut and 'mut' in bid.name) or (not is_mut)]
    testbenches = _load_list(base_dir, dd, "testbenches", _load_testbench)
    assert len(testbenches) > 0, "No testbench in project.toml!"
    design = Design(
        top=top,
        directory=project_dir,
        sources=[parse_path(pp, base_dir, True) for pp in project['sources']],
    )
    return Project(name, design, bugs, testbenches)

def copy_whole_bug_dir(bug_dir: Path, working_dir: Path, exist_ok = False):
    destination_dir = working_dir / bug_dir.name
    if destination_dir.exists() and not exist_ok:
        shutil.rmtree(destination_dir)
    if destination_dir.exists() and exist_ok:
        return
    shutil.copytree(bug_dir, destination_dir)

def pick_testbench(project: Project, testbench: str = None, bug: str = None) -> Testbench:
    assert len(project.testbenches) > 0
    return _filter_tbs(project.testbenches, testbench, bug)[0]

def pick_mut_testbenches(project: Project) -> List[Testbench]:
    return [tb for tb in project.testbenches if 'mut' in tb.name]

def _filter_tbs(tbs: list, testbench: str, bug: str) -> list:
    # if a testbench of a particular name is specified, then we just look for that bench and ignore whether it is
    # suitable for a particular bug
    if testbench is not None:
        return [tb for tb in tbs if tb.name == testbench]
    elif bug is not None:
        return [tb for tb in tbs if (tb.bugs is None) or (bug in tb.bugs)]
    else:
        return tbs

def pick_oracle_testbench(project: Project, testbench: str = None, bug: str = None) -> VerilogOracleTestbench:
    tbs = [tb for tb in project.testbenches if isinstance(tb, VerilogOracleTestbench)]
    assert len(tbs) > 0, f"No VerilogOracleTestbench available for project {project.name}."
    return _filter_tbs(tbs, testbench, bug)[0]

def pick_trace_testbench(project: Project, testbench: str = None, bug: str = None) -> TraceTestbench:
    tbs = [tb for tb in project.testbenches if isinstance(tb, TraceTestbench)]
    assert len(tbs) > 0, f"No TraceTestbench available for project {project.name}."
    return _filter_tbs(tbs, testbench, bug)[0]

def get_benchmarks(project: Project, testbench: str = None, is_mut: bool = False) -> list:
    if not is_mut:
        tb = pick_testbench(project, testbench)
        return [Benchmark(project.name, project.design, bb, tb) for bb in project.bugs if bb.name in tb.name]
    else:
        tbs = pick_mut_testbenches(project)
        res = []
        for tb in tbs:
            res.extend([Benchmark(project.name, project.design, bb, tb) for bb in project.bugs if tb.name.endswith(bb.name)])
        return res

def get_benchmark(project: Project, bug_name: str, testbench: str = None, use_trace_testbench: bool = False) -> Benchmark:
    if use_trace_testbench:
        tb = pick_trace_testbench(project, testbench, bug=bug_name)
    else:
        tb = pick_testbench(project, testbench, bug=bug_name)

    if bug_name is None:    # no bug --> create a benchmark from the original circuit
        original = project.design.sources[0]
        bb = Bug(name="original", original=original, buggy=original)
        return Benchmark(project.name, project.design, bb, tb)

    for bb in project.bugs:
        if bb.name == bug_name:
            return Benchmark(project.name, project.design, bb, tb)
    raise KeyError(f"Failed to find bug `{bug_name}`: {[bb.name for bb in project.bugs]}")

def get_other_sources(benchmark: Benchmark) -> list:
    """ returns a list of sources which are not the buggy source """
    return [s for s in benchmark.design.sources if s != benchmark.bug.original]

def get_benchmark_design(benchmark: Benchmark) -> Design:
    """ replaces the original file with the buggy one """
    orig = benchmark.design
    sources = get_other_sources(benchmark) + [benchmark.bug.buggy]
    return Design(top=orig.top, directory=orig.directory, sources=sources)

def get_seed(benchmark: Benchmark) -> Optional[str]:
    try:
        return cirfix_seeds[benchmark.project_name][benchmark.bug.name]
    except KeyError:
        return None


def is_cirfix_paper_benchmark(benchmark: Benchmark) -> bool:
    return (benchmark.project_name in cirfix_seeds and
            benchmark.bug.name in cirfix_seeds[benchmark.project_name])

def is_cirfix_paper_project(project: Project) -> bool:
    return project.name in cirfix_seeds or project.name in {'sha3_padder', 'sha3_f_permutation'}

def is_fpga_debugging_benchmark(benchmark: Benchmark) -> bool:
    return benchmark.project_name in fpga_projects


def assert_file_exists(name: str, filename: Path):
    assert filename.exists(), f"{name}: {filename} not found!"
    assert filename.is_file(), f"{name}: {filename} is not a file!"


def assert_dir_exists(name: str, filename: Path):
    assert filename.exists(), f"{name}: {filename} not found!"
    assert filename.is_dir(), f"{name}: {filename} is not a directory!"


def _check_unique_name(project_name: str, names: list[str], kind: str):
    other_names = set()
    for name in names:
        assert name not in other_names, (f"{project_name}: {name} is already used by another {kind} entry. "
        f"All {kind}s are required to have unique names!")
        other_names.add(name)


def validate_project(project: Project):
    assert_dir_exists(project.name, project.design.directory)
    for source in project.design.sources:
        assert_file_exists(project.name, source)
    for bug in project.bugs:
        validate_bug(project, bug)
    for tb in project.testbenches:
        validate_testbench(project, tb)
    _check_unique_name(project.name, [tb.name for tb in project.testbenches], "testbench")
    _check_unique_name(project.name, [bb.name for bb in project.bugs], "bug")


def validate_bug(project: Project, bug: Bug):
    name = f"{project.name}.{bug.name}"
    assert_file_exists(name, bug.original)
    assert_file_exists(name, bug.buggy)
    assert bug.original in project.design.sources, f"{name}: {bug.original} is not a project source!"


def validate_testbench(project: Project, testbench: Testbench):
    if isinstance(testbench, VerilogOracleTestbench):
        validate_oracle_testbench(project, testbench)


def validate_oracle_testbench(project: Project, testbench: VerilogOracleTestbench):
    name = f"{project.name}.{testbench.name}"
    for source in testbench.sources:
        assert_file_exists(name, source)
        assert source not in project.design.sources, f"{name}: {source} is already a project source!"
    for init in testbench.init_files:
        assert_file_exists(name, init)
    assert_file_exists(name, testbench.oracle)

def load_all_projects() -> dict:
    pps = {}
    for name, directory in projects.items():
        pps[name] = load_project(directory)
    return pps

def load_fpga_projects(is_mut: bool = False) -> dict:
    pps = {}
    if not is_mut:
        filter_projs = [
            's1', 's2', 's3', 'c4', 'd4', 'd12', 'd11', 'd13',
            'd8',
            'c1',
            'c3',
            'd9'
          ]
    else:
        filter_projs = ['c4', 'd4', 'd11', 'd12', 'd13', 's1', 's2', 's3']
    for proj in _fpga_dir.glob('*'):
        if not proj.is_dir():
            continue
        if not proj.name[:proj.name.find('-')] in filter_projs:
            continue
        # for bug in proj.glob('*'):
        #     if not bug.is_dir():
        #         continue
        pps[proj.name] = load_project(proj, is_mut)
    return pps

def load_a4v_projects() -> dict:
    pps = {}
    for proj in _a4v_dir.glob('*'):
        if not proj.is_dir():
            continue
        for bug in proj.glob('*'):
            if not bug.is_dir():
                continue
            pps[bug.name] = load_project(bug)
    return pps

def load_hw_cwes_projects() -> dict:
    pps = {}
    for proj in _hw_cwes_dir.glob('*'):
        if not proj.is_dir():
            continue
        for bug in proj.glob('*'):
            if not bug.is_dir():
                continue
            pps[bug.name] = load_project(bug)
    return pps

def load_benchmark_by_name(project_name: str, bug_name: str, tb_name: str = None) -> Benchmark:
    project = load_project(projects[project_name])
    bench = get_benchmark(project, bug_name, tb_name)
    return bench
