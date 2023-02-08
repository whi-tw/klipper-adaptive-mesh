import importlib.util
import sys
from pathlib import Path
from typing import List

import pytest

from fake_printer.fake_printer import FakePrinter


@pytest.fixture
def fake_printer():
    template_path = Path("./macros/EXCLUDE_OBJECT_START.gcode").absolute()
    fake_printer = FakePrinter(template_path.parent)
    fake_printer.load_template(template_path.name)
    return fake_printer


@pytest.fixture
def variables():
    vars_spec = importlib.util.spec_from_file_location(
        "my_vars", "./macros/EXCLUDE_OBJECT_START.vars.py"
    )
    vars = importlib.util.module_from_spec(vars_spec)
    sys.modules["my_vars"] = vars
    vars_spec.loader.exec_module(vars)
    return vars.MACRO_VARS


@pytest.mark.parametrize(
    "object_name,created_mesh_names,bed_mesh_profiles,current_mesh,expected",
    [
        pytest.param(
            "some_object",
            ["ABM_SOME_OBJECT", "default"],
            {"ABM_SOME_OBJECT": {}, "default": {}},
            "",
            ["BED_MESH_PROFILE LOAD=ABM_SOME_OBJECT"],
            id="created_by_us-mesh_exists-default_exists-default_was_created_by_us",
        ),
        pytest.param(
            "some_object",
            ["ABM_SOME_OTHER_OBJECT"],
            {"ABM_SOME_OBJECT": {}, "default": {}},
            "",
            ["BED_MESH_PROFILE LOAD="],
            marks=pytest.mark.xfail(strict=True),  # should fail
            id="not_created_by_us-mesh_exists",
        ),
        pytest.param(
            "some_object",
            ["ABM_SOME_OBJECT"],
            {"ABM_SOME_OTHER_OBJECT": {}, "default": {}},
            "",
            ["BED_MESH_PROFILE LOAD="],
            marks=pytest.mark.xfail(strict=True),  # should fail
            id="created_by_us-mesh_does_not_exist",
        ),
        pytest.param(
            "some_object",
            ["ABM_SOME_OTHER_OBJECT"],
            {"ABM_SOME_OTHER_OBJECT": {}},
            "",
            ["BED_MESH_PROFILE LOAD="],
            marks=pytest.mark.xfail(strict=True),  # should fail
            id="not_created_by_us-mesh_does_not_exist",
        ),
        pytest.param(
            "some_object",
            ["ABM_SOME_OTHER_OBJECT", "default"],
            {"ABM_SOME_OTHER_OBJECT": {}, "default": {}},
            "",
            ["BED_MESH_PROFILE LOAD=default"],
            id="not_created_by_us-mesh_does_not_exist-default_exists-default_was_created_by_us",  # noqa: E501
        ),
        pytest.param(
            "some_object",
            ["ABM_SOME_OTHER_OBJECT"],
            {"ABM_SOME_OTHER_OBJECT": {}, "default": {}},
            "",
            ["BED_MESH_PROFILE LOAD="],
            marks=pytest.mark.xfail(strict=True),  # should fail
            id="not_created_by_us-mesh_does_not_exist-default_exists-default_was_not_created_by_us",  # noqa: E501
        ),
        pytest.param(
            "some_object",
            ["ABM_SOME_OBJECT"],
            {"ABM_SOME_OBJECT": {}, "default": {}},
            "ABM_SOME_OBJECT",
            ["BED_MESH_PROFILE LOAD=ABM_SOME_OBJECT"],
            marks=pytest.mark.xfail(strict=True),  # should fail
            id="mesh-already-loaded",  # noqa: E501
        ),
    ],
)
def test_mesh_is_loaded_when_it_should_be(
    object_name: str,
    created_mesh_names: List[str],
    bed_mesh_profiles: dict,
    current_mesh: str,
    expected: List[str],
    fake_printer: FakePrinter,
    variables: dict,
):
    fake_printer.printer.bed_mesh.profiles = bed_mesh_profiles
    fake_printer.printer.bed_mesh.profile_name = current_mesh
    fake_printer.printer[
        "gcode_macro BED_MESH_CALIBRATE"
    ].created_mesh_names = created_mesh_names
    output = fake_printer.render(params={"NAME": object_name}, **variables)
    for line in expected:
        assert line in output


def test_original_gcode_is_called(fake_printer: FakePrinter, variables: dict):
    output = fake_printer.render(
        params={"NAME": "some_object"}, rawparams="NAME=some_object", **variables
    )
    assert "_EXCLUDE_OBJECT_START NAME=some_object" in output
