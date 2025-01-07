# SRepair: Symbolic Regression-Based Repair for Hardware Design Code

Welcome to the official repository for **SRepair**, a novel approach leveraging symbolic regression for repairing hardware design code. This repository contains all the necessary resources to reproduce the experiments and evaluate the methodology proposed in our paper.

## Repository Overview

This repository includes:

- **Source Code**: Implementation of the SRepair approach, including symbolic regression algorithms and repair logic tailored for hardware design code.
- **Experiment Results**: Detailed results of the experiments conducted to evaluate SRepair.
- **Datasets**: Hardware design code samples used during our experiments.
- **Scripts**: Tools for running experiments, reproducing results, and generating visualizations.

## How to Use This Repository

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/anonymous-ac-516/SRepair.git
   cd SRepair
   ```

2. **Set Up the Environment**:
   Our approach builds upon RTL-Repair. Follow the instructions in the [RR-README](rtl-repair/RR-README.md) to install dependencies and configure the environment.

3. **Run Experiments**:
   See the [docs](./docs) for detailed instructions.

4. **Explore the Results**:
   Results are organized in the `results/` or `results-aug/` directories.

## Symbolic Regression Network

SRepair addresses the challenges of synthesize complex expressions for hardware design code by utilizing a novel Symbolic Regression Network (SRN), whcih serves as the core component of SRepair. To demonstrate the fundamental concept of SRN, we provide a simple example implementation in [srn_demo.py](srn_demo.py).

In this demo, the goal is for SRN to infer the underlying mapping relationship from a given set of input-output data.

For this example, the target function is defined as: `y = x[0] + ~x[1] + ~x[2]`

We generate input data randomly and compute the corresponding output values using the above function. These data pairs are then fed into the SRN, which is designed to predict the relationship without any explicit knowledge of the function's mathematical expression.
