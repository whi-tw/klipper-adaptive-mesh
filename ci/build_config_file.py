#!/usr/bin/env python

import importlib.util
import sys
from pathlib import Path

import jinja2

template_file = Path(sys.argv[1]).absolute()
macros_dir = Path(sys.argv[2]).absolute()
version = sys.argv[3]
output_file = Path(sys.argv[4]).absolute()

env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_file.parent))

template = env.get_template(template_file.name)

macros = []

macro_gcode_files = macros_dir.glob("*.gcode")
macro_gcode_files = sorted(macro_gcode_files)
for macro_gcode_file in macro_gcode_files:
    macro_name = macro_gcode_file.stem
    macro = {"name": macro_name, "gcode": macro_gcode_file.read_text()}

    if (macros_dir / f"{macro_name}.vars.py").is_file():
        macro_vars_spec = importlib.util.spec_from_file_location(
            f"{macro_name}_vars", f"./macros/{macro_name}.vars.py"
        )
        macro_vars = importlib.util.module_from_spec(macro_vars_spec)
        sys.modules[f"{macro_name}_vars"] = macro_vars
        macro_vars_spec.loader.exec_module(macro_vars)
        if hasattr(macro_vars, "MACRO_VARS_SECTIONS"):
            macro["variables"] = macro_vars.MACRO_VARS_SECTIONS
        if hasattr(macro_vars, "rename_existing"):
            macro["rename_existing"] = macro_vars.rename_existing
        if hasattr(macro_vars, "description"):
            macro["description"] = macro_vars.description

    macros.append(macro)

rendered_file = template.render(macros=macros, version=version)

output_dir = Path(output_file).parent.absolute()

output_dir.mkdir(exist_ok=True)
output_file.write_text(rendered_file)
