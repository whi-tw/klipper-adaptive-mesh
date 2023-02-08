import importlib.util
import sys
from pathlib import Path
from typing import List, Tuple

import pytest

from fake_printer.fake_printer import FakePrinter


@pytest.fixture
def fake_printer():
    template_path = Path("./macros/BED_MESH_CALIBRATE.gcode").absolute()
    fake_printer = FakePrinter(template_path.parent)
    fake_printer.load_template(template_path.name)

    # Set default values for the mesh parameters
    fake_printer.printer.configfile.settings.bed_mesh.mesh_min = (25, 25)
    fake_printer.printer.configfile.settings.bed_mesh.mesh_max = (275, 275)
    fake_printer.printer.configfile.settings.bed_mesh.probe_count = (7, 7)

    return fake_printer


@pytest.fixture
def variables():
    vars_spec = importlib.util.spec_from_file_location(
        "my_vars", "./macros/BED_MESH_CALIBRATE.vars.py"
    )
    vars = importlib.util.module_from_spec(vars_spec)
    sys.modules["my_vars"] = vars
    vars_spec.loader.exec_module(vars)

    # Explicitely enable per object meshing by default
    vars.MACRO_VARS["per_object_mesh_enable"] = True

    return vars.MACRO_VARS


@pytest.mark.parametrize(
    "objects,expected",
    [
        pytest.param(
            [
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
            ],
            [
                "_BED_MESH_CALIBRATE PROFILE=ABM_OBJECT MESH_MIN=100.000,100.000 MESH_MAX=200.000,200.000 ALGORITHM=lagrange PROBE_COUNT=4,4 RELATIVE_REFERENCE_INDEX=-1",  # noqa: E501
            ],
            id="when_there_was_a_single_object",
        ),
        pytest.param(
            [
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
            ],
            [
                "_BED_MESH_CALIBRATE PROFILE=ABM_OBJECT MESH_MIN=100.000,100.000 MESH_MAX=200.000,200.000 ALGORITHM=lagrange PROBE_COUNT=4,4 RELATIVE_REFERENCE_INDEX=-1",  # noqa: E501
                "_BED_MESH_CALIBRATE PROFILE=ABM_OBJECT1 MESH_MIN=50.000,50.000 MESH_MAX=100.000,100.000 ALGORITHM=lagrange PROBE_COUNT=3,3 RELATIVE_REFERENCE_INDEX=-1",  # noqa: E501
            ],
            id="when_there_were_multiple_objects",
        ),
    ],
)
def test_BED_MESH_CALIBRATE_is_called_with_correct_params_if_per_object_mesh_enabled(  # noqa: E501
    objects: List[dict], expected: List[str], fake_printer: FakePrinter, variables: dict
):
    fake_printer.printer.exclude_object.objects = objects
    output = fake_printer.render(**variables)
    for expected_outout in expected:
        assert expected_outout in output

    assert "ABM: Not creating individual object meshes" not in output


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


@pytest.mark.parametrize(
    "object,algorithm",
    [
        pytest.param(
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
            "lagrange",
            id="when_the_object_is_small",
        ),
        pytest.param(
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
            "bicubic",
            id="when_the_object_is_large",
        ),
    ],
)
def test_algorithm_is_set_correctly_by_object_size(
    object: dict, algorithm: str, fake_printer: FakePrinter, variables: dict
):
    fake_printer.printer.exclude_object.objects = [object]

    output = fake_printer.render(**variables)
    assert f"ALGORITHM={algorithm}" in output


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


@pytest.mark.parametrize(
    "objects,expected",
    [
        pytest.param(
            [
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
            ],
            "SET_GCODE_VARIABLE MACRO=BED_MESH_CALIBRATE VARIABLE=created_mesh_names VALUE='[\"ABM_OBJECT\"]'",  # noqa: E501
            id="when_there_was_a_single_object",
        ),
        pytest.param(
            [
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
            ],
            'SET_GCODE_VARIABLE MACRO=BED_MESH_CALIBRATE VARIABLE=created_mesh_names VALUE=\'["ABM_OBJECT", "ABM_OBJECT1"]\'',  # noqa: E501
            id="when_there_were_multiple_objects",
        ),
    ],
)
def test_created_mesh_names_variable_should_be_created_correctly(
    objects: List[dict], expected: str, fake_printer: FakePrinter, variables: dict
):
    fake_printer.printer.exclude_object.objects = objects

    output = fake_printer.render(**variables)
    assert expected in output


@pytest.mark.parametrize(
    "created_mesh_names,bed_mesh_profiles,expected",
    [
        pytest.param(
            ["SOME_OLD_OBJECT"],
            {"SOME_OLD_OBJECT": {}},
            ["BED_MESH_PROFILE REMOVE=SOME_OLD_OBJECT"],
            id="when_there_was_a_single_object",
        ),
        pytest.param(
            ["SOME_OLD_OBJECT", "ANOTHER_OLD_OBJECT"],
            {
                "SOME_OLD_OBJECT": {},
                "ANOTHER_OLD_OBJECT": {},
            },
            [
                "BED_MESH_PROFILE REMOVE=SOME_OLD_OBJECT",
                "BED_MESH_PROFILE REMOVE=ANOTHER_OLD_OBJECT",
            ],
            id="when_there_were_multiple_objects",
        ),
    ],
)
def test_old_meshes_are_deleted_when_they_should_be(
    created_mesh_names: List[str],
    bed_mesh_profiles: dict,
    expected: List[str],
    fake_printer: FakePrinter,
    variables: dict,
):
    variables["created_mesh_names"] = created_mesh_names
    fake_printer.printer.bed_mesh.profiles = bed_mesh_profiles
    output = fake_printer.render(**variables)
    for line in expected:
        assert line in output


@pytest.mark.parametrize(
    "per_object_mesh_enable,multi_mesh_max_objects,objects,expected",
    [
        pytest.param(
            False,
            5,
            [
                {
                    "center": [150.0, 150.0],
                    "polygon": [
                        [100.0, 100.0],
                        [100.0, 200.0],
                        [200.0, 200.0],
                        [200.0, 100.0],
                    ],
                    "name": "object",
                }
            ],
            [
                "_BED_MESH_CALIBRATE PROFILE=default MESH_MIN=100.000,100.000 MESH_MAX=200.000,200.000 ALGORITHM=lagrange PROBE_COUNT=4,4 RELATIVE_REFERENCE_INDEX=-1"  # noqa: E501
            ],
            id="when_per_object_mesh_enable_is_false",
        ),
        pytest.param(
            True,
            5,
            [],
            [
                "_BED_MESH_CALIBRATE PROFILE=default MESH_MIN=25.000,25.000 MESH_MAX=275.000,275.000 ALGORITHM=bicubic PROBE_COUNT=7,7 RELATIVE_REFERENCE_INDEX=-1"  # noqa: E501
            ],
            id="when_there_are_no_objects",
        ),
        pytest.param(
            True,
            1,
            [
                {
                    "center": [75.0, 75.0],
                    "polygon": [
                        [50.0, 50.0],
                        [50.0, 100.0],
                        [100.0, 100.0],
                        [100.0, 500.0],
                    ],
                    "name": "object",
                },
                {
                    "center": [150.0, 150.0],
                    "polygon": [
                        [100.0, 100.0],
                        [100.0, 200.0],
                        [200.0, 200.0],
                        [200.0, 100.0],
                    ],
                    "name": "object1",
                },
            ],
            [
                "_BED_MESH_CALIBRATE PROFILE=default MESH_MIN=50.000,50.000 MESH_MAX=200.000,275.000 ALGORITHM=bicubic PROBE_COUNT=5,7 RELATIVE_REFERENCE_INDEX=-1"  # noqa: E501
            ],
            id="when_there_are_more_objects_than_multi_mesh_max_objects",
        ),
        pytest.param(
            True,
            2,
            [
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
                        [100.0, 100.0],
                        [100.0, 200.0],
                        [200.0, 200.0],
                        [200.0, 100.0],
                    ],
                    "name": "object1",
                },
            ],
            ["_BED_MESH_CALIBRATE PROFILE=default"],
            marks=pytest.mark.xfail(strict=True),  # should fail
            id="when_there_are_fewer_objects_than_multi_mesh_max_objects",
        ),
    ],
)
def test_global_adaptive_mesh_is_created_if_it_should_be(
    per_object_mesh_enable: bool,
    multi_mesh_max_objects: int,
    objects: List[dict],
    expected: List[str],
    fake_printer: FakePrinter,
    variables: dict,
):
    variables["per_object_mesh_enable"] = per_object_mesh_enable
    variables["multi_mesh_max_objects"] = multi_mesh_max_objects
    variables["fuzz_enable"] = False

    fake_printer.printer.exclude_object.objects = objects
    fake_printer.printer.configfile.settings.bed_mesh.mesh_min = (25, 25)
    fake_printer.printer.configfile.settings.bed_mesh.mesh_max = (275, 275)
    fake_printer.printer.configfile.settings.bed_mesh.probe_count = (7, 7)

    output = fake_printer.render(**variables)
    for line in expected:
        assert line in output


@pytest.mark.parametrize(
    "mesh_min,mesh_max,probe_count,objects,expected",
    [
        pytest.param(
            (23, 23),
            (271, 271),
            (7, 7),
            [
                {
                    "center": [150.0, 150.0],
                    "polygon": [
                        [5.0, 5.0],
                        [5.0, 300.0],
                        [200.0, 300.0],
                        [200.0, 5.0],
                    ],
                    "name": "object",
                },
            ],
            ["MESH_MIN=23.000,23.000", "MESH_MAX=200.000,271.000"],
            id="when_there_are_fewer_objects_than_multi_mesh_max_objects",
        ),
        pytest.param(
            (5, 5),
            (295, 295),
            (7, 7),
            [
                {
                    "center": [150.0, 150.0],
                    "polygon": [
                        [5.0, 5.0],
                        [5.0, 280.0],
                        [200.0, 280.0],
                        [200.0, 5.0],
                    ],
                    "name": "object",
                },
            ],
            ["MESH_MIN=5.000,5.000", "MESH_MAX=200.000,280.000"],
            id="when_there_are_fewer_objects_than_multi_mesh_max_objects",
        ),
    ],
)
def test_global_adaptive_mesh_clamps_to_klipper_bed_mesh_config(
    mesh_min: Tuple[float, float],
    mesh_max: Tuple[float, float],
    probe_count: Tuple[int, int],
    objects: List[dict],
    expected: str,
    fake_printer: FakePrinter,
    variables: dict,
):
    variables["per_object_mesh_enable"] = False
    variables["fuzz_enable"] = False

    fake_printer.printer.exclude_object.objects = objects
    fake_printer.printer.configfile.settings.bed_mesh.mesh_min = mesh_min
    fake_printer.printer.configfile.settings.bed_mesh.mesh_max = mesh_max
    fake_printer.printer.configfile.settings.bed_mesh.probe_count = probe_count

    output = fake_printer.render(**variables)
    print(output)
    for line in expected:
        assert line in output
