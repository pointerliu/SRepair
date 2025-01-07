## 1. Environment Setup

Ensure you have the required dependencies installed. You can use the following steps to set up the environment.

The source code for RTL-Repair is located in [rtl-repair](../rtl-repair/).

### 1.1 Prerequisites

- Icarus Verilog version 12.0
- Rust >= 1.80

### 1.2 Build Synthesizer

Compile and build the synthesizer for RTL-Repair.

```sh
cd synth
cargo build --release
cd ..
```

### 1.3 Open-Source Verilog Simulators, SMT Solvers and the Yosys Synthesis Tool

Download [OSS CAD Suite version `2022-06-22` from github](https://github.com/YosysHQ/oss-cad-suite-build/releases/tag/2022-06-22) and put the binaries on your path.

_Note: newer versions of the OSS CAD Suite include Verilator 5. Unfortunately, the current implementation of RTL-Repair only works with Verilator 4._

Check to make sure that you have all tools that we require on your path in the correct version:

```sh
$ verilator --version
Verilator 4.225 devel rev v4.224-91-g0eeb40b9

$ bitwuzla --version
1.0-prerelease

$ iverilog -v
Icarus Verilog version 12.0 (devel) (s20150603-1556-g542da1166)

$ yosys -version
Yosys 0.18+29
```

```sh
export PATH=/path/to/oss-cad-suite/bin:$PATH
```

### 1.4 Environment

```sh
cd rtl-repair
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# make working dir for Cirfix at the root folder
mkdir rtl-repair-repairs
```

## 2. Experiment Conduction

#### 2.1 cirfix-benchmark (~25min)

```sh
./scripts/run_rtl_repair_experiment.py --working-dir=exp_oct/rtl-repair-repairs/cirfix --clear --experiment=default --tag=RR
```

#### 2.2 HW-CWEs (~1min)

```sh
python run_ext_bench.py --method=RR --dataset=HW_CWEs --wk_dir=exp_oct/rtl-repair-repairs/HW_CWEs --timeout 300
```

#### 2.3 Assignment4V (~1min)

```sh
python run_ext_bench.py --method=RR --dataset=Assignment4V --wk_dir=exp_oct/rtl-repair-repairs/Assignment4V --timeout 300
```

#### 2.4 fpga-debugging (~35min)

```sh
./scripts/run_rtl_repair_experiment.py --working-dir=exp_oct/rtl-repair-repairs/fpga-debugging --clear --experiment=fpga-all --tag=RR
```
