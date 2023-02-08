import importlib.util
import sys
from pathlib import Path


class SettingsBedMesh:
    mesh_min = (25, 25)
    mesh_max = (275, 275)
    probe_count = (7, 7)


class Settings:
    bed_mesh = SettingsBedMesh()


class ConfigFile:
    settings = Settings()


class ExcludeObject:
    objects = []


class BedMesh:
    profiles = {}


class Macro:
    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


class Printer(dict):
    configfile = ConfigFile()
    exclude_object = ExcludeObject()
    bed_mesh = BedMesh()

    def __init__(self):
        super().__init__(self)

        macro_vars_files = Path("./macros").absolute().glob("*.vars.py")

        for macro in macro_vars_files:
            macro_name = macro.stem.removesuffix(".vars")
            dict_item_name = f"gcode_macro {macro_name}"
            vars_spec = importlib.util.spec_from_file_location(
                "macro_vars", "./macros/BED_MESH_CALIBRATE.vars.py"
            )
            vars = importlib.util.module_from_spec(vars_spec)
            sys.modules["my_vars"] = vars
            vars_spec.loader.exec_module(vars)
            self[dict_item_name] = Macro(**vars.MACRO_VARS)
