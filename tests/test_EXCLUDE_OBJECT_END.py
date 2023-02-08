import importlib.util
import sys
from pathlib import Path
from typing import List

import pytest

from fake_printer.fake_printer import FakePrinter


@pytest.fixture
def fake_printer():
    template_path = Path("./macros/EXCLUDE_OBJECT_END.gcode").absolute()
    fake_printer = FakePrinter(template_path.parent)
    fake_printer.load_template(template_path.name)
    return fake_printer


@pytest.fixture
def variables():
    vars_spec = importlib.util.spec_from_file_location(
        "my_vars", "./macros/EXCLUDE_OBJECT_END.vars.py"
    )
    vars = importlib.util.module_from_spec(vars_spec)
    sys.modules["my_vars"] = vars
    vars_spec.loader.exec_module(vars)
    return vars.MACRO_VARS


@pytest.mark.parametrize(
    "created_mesh_names",
    [
        pytest.param([], id="no_meshes_created"),
        pytest.param(["default"], id="default_mesh_created"),
    ],
)
def test_mesh_not_cleared_if_not_required(
    created_mesh_names: List[str], fake_printer: FakePrinter, variables: dict
):
    fake_printer.printer[
        "gcode_macro BED_MESH_CALIBRATE"
    ].created_mesh_names = created_mesh_names
    output = fake_printer.render(**variables)
    assert "BED_MESH_CLEAR" not in output


@pytest.mark.parametrize(
    "created_mesh_names",
    [
        pytest.param(["some_mesh"], id="single_mesh_created"),
        pytest.param(["some_mesh", "some_other_mesh"], id="multiple_meshes_created"),
        pytest.param(
            ["some_mesh", "some_other_mesh", "default"],
            id="multiple_meshes_created_with_default",
        ),
    ],
)
def test_mesh_cleared_if_mesh_was_created(
    created_mesh_names: List[str], fake_printer: FakePrinter, variables: dict
):
    fake_printer.printer[
        "gcode_macro BED_MESH_CALIBRATE"
    ].created_mesh_names = created_mesh_names
    output = fake_printer.render(**variables)

    assert "BED_MESH_CLEAR" in output


def test_original_gcode_is_called(fake_printer: FakePrinter, variables: dict):
    output = fake_printer.render(
        params={"NAME": "some_object"}, rawparams="NAME=some_object", **variables
    )
    assert "_EXCLUDE_OBJECT_END NAME=some_object" in output
