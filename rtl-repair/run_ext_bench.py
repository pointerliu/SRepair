"""
--project /home/lzz/hAPR/rtl-repair/benchmarks/Assignment4V/decoder3e/decoder3e_1
--solver bitwuzla
--working-dir /home/lzz/hAPR/rtl-repair/scripts/rtl-repair-a4v/decoder3e/decoder3e_1
--init random
--bug decoder3e_1
--testbench decoder3e_tb.v
--incremental
--verbose-synthesizer

"""
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
from collections import defaultdict
from pathlib import Path
from argparse import ArgumentParser
from threading import Thread

import tomli
from queue import Queue

LIMIT = -1
TIMEOUT = 180
# BOUND_ARCH = '3,2,1'
bound_arch = {
    3: '3,2,1',
    2: '2,1',
    1: '1'
}

BOUND_ARCH = ''


# BOUND_ARCH = '1'


def worker(cfg, method_dir, bug_dir, data_set, templates, out_dir, wk_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        cmd = [
            "python",
            str(Path(__file__).parent.resolve() / 'rtlrepair.py'),
            f'--project',
            f'{bug_dir}',
            '--solver',
            'bitwuzla',
            f'--working-dir',
            str(out_dir),
            '--init',
            'zero' if 'fpga' in data_set else 'random',
            f'--bug',
            f'{bug_dir.name}',
            f'--testbench',
            f'{bug_dir.parent.name}_tb.v',
            '--templates',
            templates,
            '--incremental',
            '--verbose-synthesizer',
            # '--run-all-templates' if cfg.run_all_templates else '',
            # when testing mutation, pls skip-preprocessing
            # '--skip-preprocessing',
            # '--timeout',
            # f'{TIMEOUT}',
            # f'--bound-arch' if len(BOUND_ARCH) != 0 else '',
            # {BOUND_ARCH} if len(BOUND_ARCH) != 0 else '',
        ]
        if len(BOUND_ARCH) != 0:
            cmd.extend([
                '--bound-arch',
                BOUND_ARCH,
            ])

        if cfg.run_all_templates:
            cmd.append('--run-all-templates')
            cmd.append('--template-timeout')
            cmd.append(f'{TIMEOUT}')
        else:
            cmd.append('--timeout')
            cmd.append(f'{TIMEOUT}')
        print(' '.join(cmd))
        ret = subprocess.run(
            cmd, check=True,
            # cwd=f'{cfg.wk_dir}/..'
        )
    except Exception as e:
        # print(e)
        return None

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
    return status


def do_eval_assignment4v(cfg):
    # data_set = "Assignment4V"
    # data_set = "HW_CWEs"
    # data_set = "fpga-mutation"
    # data_set = "default"
    data_set = cfg.dataset
    method = cfg.method
    # method = "RR"

    if method == "SNN":
        if "mutation" in data_set:
            templates = ','.join([
                't1_replace_atom',
                # 't2_replace_cond',
                't3_replace_assign',
                't4_add_substitution',
                # 't5_change_timing_assign',
                # 't5_change_timing_subs_pre',
                # 't5_change_timing_subs_post'
            ])
        else:
            templates = ','.join([
                't1_replace_atom',
                't2_replace_cond',
                't3_replace_assign',
                't4_add_substitution',
                't5_change_timing_assign',
                't5_change_timing_subs_pre',
                't5_change_timing_subs_post'
            ])
    elif method == "RR":
        templates = ','.join([
            'replace_literals',
            'add_guard',
            'conditional_overwrite'
        ])
    elif method == "RR_SNN":
        templates = ','.join([
            'replace_literals',
            't3_replace_assign_rr_t',
            't6_cond_overwrite_rr_t_pre',
            't6_cond_overwrite_rr_t_post',
        ])
    elif method == "SNN_RR":
        templates = ','.join([
            't1_replace_atom',
            't3_replace_assign_rr_synth',
            't4_add_substitution_rr_synth'
        ])
    else:
        raise NotImplementedError(f"Method {method} not implemented")

    method_dir = f"repair-{data_set}-{method}"

    st_res = []

    for proj in (Path(__file__).parent / f'benchmarks/{data_set}').glob('*'):
        if not proj.is_dir(): continue
        # ignore counters
        if proj.stem in [
            # 'mut_axis-frame-fifo-d11',
            # 'mut_axis-adapter-s3',
            # 'mut_axi-stream-s2',
            # 'mut_axis-fifo-d12',
            # 'mut_axis-frame-fifo-d11',
            # 'mut_axis-async-fifo-c4',
            # 'mut_zipcpu-spi-c1-c3-d9'
        ]:
            continue

        wk_dir = Path(f'{cfg.wk_dir}/{method_dir}/{proj.stem}').absolute()
        print(wk_dir)
        if not wk_dir.exists():
            wk_dir.mkdir(parents=True)
        statistics = defaultdict(int)
        thds = []
        _cnt = 0
        with ThreadPoolExecutor(
                max_workers=22 if 'zipcpu' not in proj.stem and 'axis-frame-len-d13' not in proj.stem else 1) as executor:

            for bug_dir in proj.glob('*'):
                if not bug_dir.is_dir(): continue
                _cnt += 1
                if _cnt == LIMIT:
                    break
                if (bug_dir / 'project.toml').exists():
                    thds.append(
                        executor.submit(worker, cfg, method_dir, bug_dir, data_set, templates, wk_dir / bug_dir.stem,
                                        wk_dir))

            for future in as_completed(thds):
                status = future.result()
                if status is not None:
                    statistics[status] += 1

        st_res.append((proj, statistics))
        (wk_dir / 'result.json').write_text(json.dumps(statistics))

        # thread = Thread(target=worker, args=(st_res, proj, method_dir, data_set, templates))
        # thread.start()
        # thds.append(thread)

    for st in st_res:
        print(st)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--method', type=str, required=True)
    parser.add_argument('--dataset', type=str, required=True)
    parser.add_argument('--wk_dir', type=str, required=True)
    parser.add_argument('--run-all-templates', action='store_true')
    parser.add_argument('--bound', type=int)
    parser.add_argument('--timeout', type=int)
    cfg = parser.parse_args()
    print(cfg)
    if cfg.bound is not None:
        BOUND_ARCH = bound_arch[cfg.bound]
    if cfg.timeout is not None:
        TIMEOUT = cfg.timeout
    do_eval_assignment4v(cfg)
