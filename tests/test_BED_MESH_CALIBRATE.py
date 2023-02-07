import importlib.util
import sys
from pathlib import Path

import pytest

from fake_printer.fake_printer import FakePrinter


@pytest.fixture
def fake_printer():
    template_path = Path("./macros/BED_MESH_CALIBRATE.gcode").absolute()
    fake_printer = FakePrinter(template_path.parent)
    fake_printer.load_template(template_path.name)
    return fake_printer


@pytest.fixture
def variables():
    vars_spec = importlib.util.spec_from_file_location(
        "my_vars", "./macros/BED_MESH_CALIBRATE.vars.py"
    )
    vars = importlib.util.module_from_spec(vars_spec)
    sys.modules["my_vars"] = vars
    vars_spec.loader.exec_module(vars)
    return vars.MACRO_VARS


def test_single_object(fake_printer: FakePrinter, variables: dict):
    objects = [
        {
            "center": [150.0, 150.0],
            "polygon": [
                [100.0, 100.0],
                [100.0, 200.0],
                [200.0, 200.0],
                [200.0, 100.0],
            ],
            "name": "object",
        },
    ]
    fake_printer.printer.exclude_object.objects = objects
    output = fake_printer.render(**variables)
    assert (
        "BED_MESH_CALIBRATE PROFILE=ABM_object MESH_MIN=100.000,100.000 MESH_MAX=200.000,200.000 ALGORITHM=lagrange PROBE_COUNT=4,4 RELATIVE_REFERENCE_INDEX=-1"
        in output
    )


def test_multi_object(fake_printer: FakePrinter, variables: dict):
    objects = [
        {
            "center": [150.0, 150.0],
            "polygon": [
                [100.0, 100.0],
                [100.0, 200.0],
                [200.0, 200.0],
                [200.0, 100.0],
            ],
            "name": "object",
        },
        {
            "center": [150.0, 150.0],
            "polygon": [
                [50.0, 50.0],
                [50.0, 100.0],
                [100.0, 100.0],
                [100.0, 50.0],
            ],
            "name": "object1",
        },
    ]
    fake_printer.printer.exclude_object.objects = objects
    output = fake_printer.render(**variables)
    assert (
        "BED_MESH_CALIBRATE PROFILE=ABM_object MESH_MIN=100.000,100.000 MESH_MAX=200.000,200.000 ALGORITHM=lagrange PROBE_COUNT=4,4 RELATIVE_REFERENCE_INDEX=-1"
        in output
    )
    assert (
        "BED_MESH_CALIBRATE PROFILE=ABM_object1 MESH_MIN=50.000,50.000 MESH_MAX=100.000,100.000 ALGORITHM=lagrange PROBE_COUNT=3,3 RELATIVE_REFERENCE_INDEX=-1"
        in output
    )


def test_single_object_near_edge_should_clamp(
    fake_printer: FakePrinter, variables: dict
):
    objects = [
        {
            "center": [50.0, 50.0],
            "polygon": [
                [0.0, 0.0],
                [0.0, 100.0],
                [100.0, 100.0],
                [100.0, 0.0],
            ],
            "name": "object",
        },
    ]
    fake_printer.printer.exclude_object.objects = objects
    fake_printer.printer.configfile.settings.bed_mesh.mesh_min = (25, 25)

    output = fake_printer.render(**variables)
    assert "MESH_MIN=25.000,25.000" in output


def test_small_object_should_be_lagrange(fake_printer: FakePrinter, variables: dict):
    objects = [
        {
            "center": [50.0, 50.0],
            "polygon": [
                [0.0, 0.0],
                [0.0, 100.0],
                [100.0, 100.0],
                [100.0, 0.0],
            ],
            "name": "object",
        },
    ]
    fake_printer.printer.exclude_object.objects = objects

    output = fake_printer.render(**variables)
    assert "ALGORITHM=lagrange" in output


def test_large_object_should_be_bicubic(fake_printer: FakePrinter, variables: dict):
    objects = [
        {
            "center": [50.0, 50.0],
            "polygon": [
                [0.0, 0.0],
                [0.0, 300.0],
                [300.0, 300.0],
                [300.0, 0.0],
            ],
            "name": "object",
        },
    ]
    fake_printer.printer.exclude_object.objects = objects

    output = fake_printer.render(**variables)
    assert "ALGORITHM=bicubic" in output


def test_long_skinny_object_should_have_different_point_count(
    fake_printer: FakePrinter, variables: dict
):
    objects = [
        {
            "center": [50.0, 50.0],
            "polygon": [
                [0.0, 0.0],
                [0.0, 10.0],
                [300.0, 10.0],
                [300.0, 0.0],
            ],
            "name": "object",
        },
    ]
    fake_printer.printer.exclude_object.objects = objects

    output = fake_printer.render(**variables)
    assert "PROBE_COUNT=7,4" in output


def test_old_meshes_are_deleted(fake_printer: FakePrinter, variables: dict):
    variables["created_mesh_names"] = "some_old_object"
    output = fake_printer.render(**variables)
    assert "BED_MESH_PROFILE DELETE=some_old_object" in output

    variables["created_mesh_names"] = "some_old_object,another_old_object"
    output = fake_printer.render(**variables)
    assert "BED_MESH_PROFILE DELETE=some_old_object" in output
    assert "BED_MESH_PROFILE DELETE=another_old_object" in output
