PROJECT_HOME    ?= $(shell pwd)
METHOD          ?= SNN
WK_DIR          ?= $(PROJECT_HOME)/exp_jul/5/ablation
TIMEOUT         ?= 120

run_aug_single:
	python $(PROJECT_HOME)/run_ext_bench.py \
	    --method=$(METHOD) \
	    --dataset=fpga-debugging-mutation-single \
	    --wk_dir=$(WK_DIR)/$(METHOD) \
	    --timeout $(TIMEOUT) \
	    --run-all-templates

run_aug_multi:
	python $(PROJECT_HOME)/run_ext_bench.py \
	    --method=$(METHOD) \
	    --dataset=fpga-debugging-mutation-multi \
	    --wk_dir=$(WK_DIR)/$(METHOD) \
	    --timeout $(TIMEOUT) \
	    --run-all-templates

.PHONY: run_aug
