# CirFix for fpga-debugging benchmark

This directory contains code based on the ASPLOS'22 artifact:
https://github.com/hammad-a/verilog_repair

We have made significant changes to allow multiple instances
of CirFix to run at the same time, but the core repair algorithm
remains unchanged and all results of the original can be reproduced.

[setup oss-cad-suite](https://github.com/YosysHQ/oss-cad-suite-build)

```bash
python run.py --working-dir=cirfix-repairs-fpga-$(date +"%Y%m%d_%H%M%S") --clear --experiment=fpga --benchmark=fpga --simulator=verilator --threads=1
```

```bash
python run.py --working-dir=cirfix-repairs-fpga-mut-$(date +"%Y%m%d_%H%M%S") --clear --experiment=fpga --benchmark=fpga --simulator=verilator --threads=1 --is-mut --runs-end 141
```