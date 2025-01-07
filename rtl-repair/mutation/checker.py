import os
import shutil
from pathlib import Path

from benchmarks.yosys import to_btor
from pyverilog.vparser.parser import VerilogCodeParser
from rtlrepair import serialize, do_repair
from rtlrepair.analysis import analyze_ast
from rtlrepair.snn_templates import add_cond_expr
from rtlrepair.synthesizer import _run_synthesizer, SynthOptions, SynthStats
from rtlrepair.snn_templates import *
from rtlrepair.utils import status_name_to_enum, Status


def check_no_repair(working_dir: Path, file_list, top_name, tb_file, init):
    if not working_dir.exists():
        working_dir.mkdir(exist_ok=True, parents=True)
    codeparser = VerilogCodeParser(
        filelist=[str(file) for file in file_list],
    )
    os.chdir(working_dir)

    ast = codeparser.parse()

    synth_filename = Path(f'{file_list[0].stem}.instrumented.v')
    with open(synth_filename, "w") as f:
        f.write(serialize(ast))

    btor_filename = to_btor(working_dir, working_dir / (synth_filename.stem + ".btor"),
                            [synth_filename], top_name,
                            script_out=working_dir / "to_botr.sh")
    opts = SynthOptions(
        solver="bitwuzla",
        init=init,
        incremental=True,
        verbose=True,
    )
    result = _run_synthesizer(working_dir, btor_filename, tb_file, opts)
    status = status_name_to_enum[result['status']]
    if status == Status.NoRepair:
        return True
    else:
        return False
