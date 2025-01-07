## 1. Environment Setup

Ensure you have the required dependencies installed. You can use the following steps to set up the environment.

The source code for Cirfix is located in [cirfix](../rtl-repair/cirfix/). It has been configured with a 12-hour timeout.

### 1.1 Prerequisites

- Icarus Verilog version 12.0

### 1.2 Environment

```sh
cd rtl-repair
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# make working dir for Cirfix at the root folder
mkdir cirfix-repairs
```

## 2. Experiment conduction

#### 2.1 cirfix-benchmark (~384 core hours)

> For the CirFix experiment on the cirfix benchmark, please refer to the [RR-README.md](../rtl-repair/RR-README.md).

#### 2.2 HW-CWEs (~120 core hours)

From the root folder please run the following (where `$N` is the number of threads):

```sh
cd rtl-repair/cirfix
./cirfix/run.py --working-dir=cirfix-repairs/HW-CWEs --clear --experiment=HW-CWEs --benchmark=HW-CWEs --simulator=iverilog --threads=$N
```

#### 2.3 Assignment4V (~624 core hours)

> For the CirFix experiment on the Assignment4V benchmark, please refer to the paper of [STRIDER](https://ieeexplore.ieee.org/abstract/document/10354074)

#### 2.4 fpga-debugging (~156 core hours)

To make Cirfix compatible to fpga-debugging benchmark, we modify the data preprocessing module of Cirfix in [cirfix-fpga](../cirfix-fpga/) folder.

```sh
cd cirfir-fpga
mkdir cirfix-repairs
./run.py --working-dir=cirfix-repairs/fpga-debugging --clear --experiment=fpga --benchmark=fpga --simulator=verilator --threads=$N
```
