#!/usr/bin/env python
import importlib.util
import sys

from .fake_printer import FakePrinter


def run_BED_MESH_CALIBRATE():
    fake_printer = FakePrinter("./macros")
    fake_printer.load_template("BED_MESH_CALIBRATE.gcode")

    objects = [
        {
            "center": [144.402, 152.574],
            "polygon": [
                [41.988, 38.988],
                [41.988, 255.012],
                [258.012, 255.012],
                [258.012, 38.988],
            ],
            "name": "object1",
        },
        {
            "center": [150, 150],
            "polygon": [
                [10.0, 52.0],
                [10.0, 92.0],
                [210.0, 92.0],
                [210.0, 52.0],
            ],
            "name": "object2_should_be_clamped",
        },
    ]

    fake_printer.printer.exclude_object.objects = objects

    vars_spec = importlib.util.spec_from_file_location(
        "my_vars", "./macros/BED_MESH_CALIBRATE.vars.py"
    )
    my_vars = importlib.util.module_from_spec(vars_spec)
    sys.modules["my_vars"] = vars
    vars_spec.loader.exec_module(my_vars)

    return fake_printer.render(**my_vars.MACRO_VARS)


macro_name = sys.argv[1]

print(locals()[f"run_{macro_name}"]())
