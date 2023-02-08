TEMPLATE := ./ci/templates/adaptive_bed_mesh.cfg.j2
MACROS_DIR := ./macros
MACROS := $(wildcard $(MACROS_DIR)/*)
BUILDER_SCRIPT := ./ci/build_config_file.py

.PHONY: all

all: output/adaptive_bed_mesh.cfg

output/adaptive_bed_mesh.cfg: $(TEMPLATE) $(BUILDER_SCRIPT) $(MACROS)
	python $(BUILDER_SCRIPT) $(TEMPLATE) $(MACROS_DIR) $@
