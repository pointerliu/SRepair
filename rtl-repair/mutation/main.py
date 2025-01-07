import concurrent
import difflib
import shutil
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from pathlib import Path
from typing import List

from mutation.checker import check_no_repair
from mutation.ops import do_expr_mutation
from pyverilog.vparser.parser import parse, VerilogCodeParser
import pyverilog.vparser.ast as vast
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
import sys, inspect, subprocess
import os, random
from optparse import OptionParser
from random import randint
import toml
from argparse import ArgumentParser

MAX_ATTEMPTS = 100


def visit_children_attr(ast):
    for child in ast.children():
        if child is not None:
            # Save the child's name and id to the dictionary
            print(vars(child))
            visit_children_attr(child)


def diff_file(text1: str, text2: str):
    diff = difflib.unified_diff(text1.splitlines(), text2.splitlines())
    res = '\n'.join(list(diff))
    return res


def get_oracle_files(base_dir: Path, meta_data: dict) -> List[Path]:
    res = []
    for f in meta_data['project']['sources']:
        res.append(base_dir / meta_data['project']['directory'] / f)
    return res


def gen_batch_expr_mutation(
        base_dir: Path,
        meta_data: dict,
        n: int,
        max_cnt: int,
        mut_var_width: str,
        out_path: Path
):
    if not out_path.exists():
        out_path.mkdir(parents=True, exist_ok=True)

    source_files = get_oracle_files(base_dir, meta_data)

    for target_file in source_files[:1]:
        codeparser = VerilogCodeParser(
            filelist=[target_file],
        )
        try:
            ast = codeparser.parse()
        except Exception as e:
            print(f'{target_file}: {e}; [ignored] !')
            continue

        codegen = ASTCodeGenerator()
        origin_code = codegen.visit(ast)

        # meta_ctx = proj_meta.read_text()

        # max_cnt = min(len(mod_pos), max_n)

        real_cnt = 0
        visited_pos = []
        for ii in range(n):

            attempts = 0
            wk_dir = out_path / f'mut_{ii}'
            if not wk_dir.exists():
                wk_dir.mkdir(parents=True, exist_ok=True)

            while attempts < MAX_ATTEMPTS:
                cpy_ast = deepcopy(ast)

                f_succ, res_ast = do_expr_mutation(cpy_ast, max_cnt, visited_pos, mut_var_width)
                if not f_succ:
                    attempts += 1
                    continue

                src_code = codegen.visit(res_ast)

                # copy buggy code
                for ff in source_files:
                    if ff == target_file:
                        with open(wk_dir / f'buggy_{ff.name}', 'w') as fp:
                            fp.write(src_code)
                    else:
                        shutil.copyfile(ff, wk_dir / ff.name)

                # copy origin code
                with open(wk_dir / f'{target_file.name}', 'w') as fp:
                    fp.write(origin_code)

                # copy meta data
                with open(wk_dir / f'project.toml', 'w') as fp:
                    # only mutate the first bug
                    meta_data['bugs'] = meta_data['bugs'][:1]

                    meta_data['bugs'][0]['buggy'] = f'buggy_{target_file.name}'
                    meta_data['bugs'][0]['name'] = f'mut_{ii}'
                    meta_data['bugs'][0]['original'] = target_file.name

                    meta_data['testbenches'] = meta_data['testbenches'][:1]
                    meta_data['testbenches'][0]['name'] = f'{out_path.name}_tb.v'

                    toml.dump(meta_data, fp)

                with open(wk_dir / f'{target_file.stem}.diff', 'w') as f:
                    f.write(diff_file(origin_code, src_code))

                used_tb_name = ''
                for tb_meta in meta_data['testbenches']:
                    tb_name = tb_meta['table'] if 'table' in tb_meta else tb_meta['oracle']
                    shutil.copyfile(f"{target_file.parent}/{tb_name}", wk_dir / tb_name)
                    if tb_meta['name'] == meta_data['testbenches'][0]['name']:
                        used_tb_name = tb_name

                assert used_tb_name != ''

                try:
                    check_ret = check_no_repair(
                        working_dir=out_path / f'wk_dir/mut_{ii}',
                        file_list=[
                            wk_dir / f'buggy_{target_file.name}' if ff == target_file else wk_dir / ff.name
                            for ff in source_files
                        ],
                        top_name=meta_data['project']['toplevel'],
                        tb_file=wk_dir / used_tb_name,
                        init="zero" if '/fpga' in str(out_path) else "random"
                    )
                except Exception as e:
                    check_ret = True

                if not check_ret:
                    real_cnt += 1
                    break
                attempts += 1
                # else:
                #     shutil.rmtree(wk_dir)
            if attempts == MAX_ATTEMPTS:
                shutil.rmtree(wk_dir)

            # with open(wk_dir / f'{file_name.name}', 'w') as f:
            #     f.write(origin_code)
            # with open(wk_dir / f'buggy_{file_name.name}', 'w') as f:
            #     f.write(src_code)

            # with open(wk_dir / f'project.toml', 'w') as f:
            # f.write(
            #     meta_ctx.
            #     replace('xlnxstream_2018_3_bug_s2.v', f'buggy_{file_name.name}').
            #     replace('"s2"', f'"mut_{ii}"').
            #     replace('"csv"', f'"{file_name.stem}_tb.v"')
            # )
            # f_meta(f, meta_ctx, file_name, ii)
            # f.write(
            #     meta_ctx.
            #     replace('axis_async_fifo_bug_c4.v', f'buggy_{file_name.name}').
            #     replace('"c4"', f'"mut_{ii}"').
            #     replace('"csv"', f'"{file_name.stem}_tb.v"')
            # )

            # f_copy(file_name.parent, wk_dir)
            # for f in src_files:
            #     shutil.copy(file_name.parent / f, wk_dir)

            # shutil.copyfile(f"{file_name.parent}/tb.csv", wk_dir / "tb.csv")

            # d3
            # shutil.copyfile(f"{file_name.parent}/axis_fifo_wrapper.v", wk_dir / "axis_fifo_wrapper.v")

            # d4
            # shutil.copyfile(f"{file_name.parent}/axis_fifo_wrapper.v", wk_dir / "axis_fifo_wrapper.v")
            # shutil.copyfile(f"{file_name.parent}/axis_register.v", wk_dir / "axis_register.v")

        print(f'{base_dir.name} gen {real_cnt}')


if __name__ == '__main__':
    # file = Path("/home/lzz/hAPR/mutaion-augumentation/data/fpga/d4/axis_async_fifo.v")
    # meta_file = Path("/home/lzz/hAPR/mutaion-augumentation/data/fpga/d4/project.toml")
    # output = Path(f"/home/lzz/hAPR/mutaion-augumentation/data/mutation/{file.stem}")
    #
    #
    # def f_meta(f, meta_ctx, file_name, id):
    #     f.write(
    #         meta_ctx.
    #         replace('axis_async_fifo_bug_c4.v', f'buggy_{file_name.name}').
    #         replace('"c4"', f'"mut_{id}"').
    #         replace('"csv"', f'"{file_name.stem}_tb.v"')
    #     )
    #
    #
    # def f_copy(src, dest):
    #     shutil.copyfile(f"{src}/tb.csv", dest / "tb.csv")
    #     shutil.copyfile(f"{src}/axis_fifo_wrapper.v", dest / "axis_fifo_wrapper.v")
    #     shutil.copyfile(f"{src}/axis_register.v", dest / "axis_register.v")

    # file = Path("/home/lzz/hAPR/mutaion-augumentation/data/fpga/d1/xlnxstream_2018_3.v")

    parser = ArgumentParser()
    parser.add_argument('--type', type=str, required=True)
    parser.add_argument('--number', type=int, default=20)
    cfg = parser.parse_args()

    original_dataset = Path("/home/lzz/hAPR/rtl-repair/benchmarks/fpga-debugging")
    # original_dataset = Path("/home/lzz/hAPR/rtl-repair/benchmarks/cirfix")

    mut_var_width = cfg.type
    # mut_var_width = 'single'
    out_path = Path(f"/home/lzz/hAPR/rtl-repair/benchmarks/{original_dataset.stem}-mutation-{mut_var_width}/")

    with ProcessPoolExecutor(max_workers=1) as executor:

        thds = []

        for base_dir in original_dataset.glob("*"):
            if not base_dir.is_dir(): continue

            # if base_dir.name != 'axi-lite-s1':
            #     continue
            if base_dir.name in [
                # 'axi-stream-s2',
                # 'axis-adapter-s3',
                # 'axis-async-fifo-c4',
                # 'axis-fifo-d4',
                # 'axis-fifo-d12',
                # 'axis-switch-d8',
                # 'axis-frame-fifo-d11',
                'zipcpu-spi-c1-c3-d9',

                # expensive mem
                # 'axis-frame-len-d13',
                'axi-lite-s1'
            ]:
                continue

            print(f'processing {base_dir}')
            # base_dir = Path("/home/lzz/hAPR/rtl-repair/benchmarks/fpga-debugging/axis-async-fifo-c4")
            meta_file = base_dir / "project.toml"
            # with open(meta_file, 'rb') as f:
            try:
                meta_data = toml.load(meta_file)
            except FileNotFoundError:
                print(f'no meta file for {base_dir}')
                continue
            # gen_batch_expr_mutation(
            #     base_dir,
            #     meta_data,
            #     300,
            #     1,
            #     out_path=Path(f"/home/lzz/hAPR/rtl-repair/benchmarks/fpga-mutation/mut_{base_dir.name}")
            # )

            thds.append(executor.submit(
                gen_batch_expr_mutation,
                base_dir,
                meta_data,
                cfg.number,
                1,
                mut_var_width,
                out_path=out_path / f'mut_{base_dir.name}'
            ))

        for future in as_completed(thds):
            future.result()

    # output = Path(f"/home/lzz/hAPR/mutaion-augumentation/data/mutation/{file.stem}")
    #
    # def f_meta(f, meta_ctx, file_name, id):
    #     f.write(
    #         meta_ctx.
    #         replace('xlnxstream_2018_3_bug_s2.v', f'buggy_{file_name.name}').
    #         replace('"s2"', f'"mut_{id}"').
    #         replace('"csv"', f'"{file_name.stem}_tb.v"')
    #     )
    #
    #
    # def f_copy(src, dest):
    #     shutil.copyfile(f"{src}/tb.csv", dest / "tb.csv")
    #     shutil.copyfile(f"{src}/xlnxstream_2018_3.v", dest / "xlnxstream_2018_3.v")
    # meta_file = Path("/home/lzz/hAPR/mutaion-augumentation/data/fpga/d3/project.toml")
    #
    # meta_data = tomli.loads(meta_file.read_text())
    #
    # file = Path("/home/lzz/hAPR/mutaion-augumentation/data/fpga/d3/axis_fifo.v")
    # output = Path(f"/home/lzz/hAPR/mutaion-augumentation/data/mutation/{file.stem}")
    #
    # def f_meta(f, meta_ctx, file_name, id):
    #     f.write(
    #         meta_ctx.
    #         replace('axis_fifo_bug_d4.v', f'buggy_{file_name.name}').
    #         replace('"d4"', f'"mut_{id}"').
    #         replace('"csv"', f'"{file_name.stem}_tb.v"')
    #     )
    #
    #
    # def f_copy(src, dest):
    #     shutil.copyfile(f"{src}/tb.csv", dest / "tb.csv")
    #     shutil.copyfile(f"{src}/axis_fifo.v", dest / "axis_fifo.v")
    #     shutil.copyfile(f"{src}/axis_fifo_wrapper.v", dest / "axis_fifo_wrapper.v")
    #
    # gen_batch_expr_mutation(file, meta_file, 300, 1, output, f_meta, f_copy)
