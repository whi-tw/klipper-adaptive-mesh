rename_existing = "_BED_MESH_CALIBRATE"
description = (
    "Calibrate the bed mesh using a probe. Adaptive mesh calibration is enabled."
)

MACRO_VARS_SECTIONS = [
    {
        "comment": "This section allows control of status LEDs your printer may have.",
        "variables": {
            "led_enable": False,
            "status_macro": "status_meshing",
        },
    },
    {
        "comment": "This section configures mesh point fuzzing, which allows probe points to be varied slightly if printing multiples of the same G-code file.",  # noqa: E501
        "variables": {
            "fuzz_enable": False,
            "fuzz_min": 0,
            "fuzz_max": 4,
        },
    },
    {
        "comment": "This section is for those using a dockable probe that is stored outside of the print area.",  # noqa: E501
        "variables": {
            "probe_dock_enable": False,
            "attach_macro": "attach_probe",
            "detach_macro": "detach_probe",
        },
    },
    {
        "comment": "This section determines the threshold for creating individual meshes vs one large mesh",  # noqa: E501
        "variables": {
            "per_object_mesh_enable": True,
            "multi_mesh_max_objects": 5,
            "multi_mesh_min_width": 100,
        },
    },
    {
        "comment": "This section contains other user-modifiable variables",
        "variables": {"verbose": True},
    },
    {
        "comment": "This section contains internal variables and should not be adjusted",  # noqa: E501
        "variables": {"created_mesh_names": []},
    },
]

MACRO_VARS = {
    key: value
    for section in MACRO_VARS_SECTIONS
    for key, value in section["variables"].items()
}
