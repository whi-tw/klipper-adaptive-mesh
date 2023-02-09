# Klipper Adaptive Bed Mesh (mesh-per-object)

## THIS IS VERY WIP

Basically, create a bed mesh for every object on the board, then load that mesh when printing that object.

## Setup

**Exclude Objects** must be configured. See the [Mainsail Docs](https://docs.mainsail.xyz/features/exclude_objects)
for a good guide on getting this set up.

Download the config file (`adaptive_bed_mesh.cfg`) from the [latest release](https://github.com/whi-tw/klipper-adaptive-mesh/releases/)
and add this to your printer. Make sure the file is included in `printer.cfg`.

## Macros

### BED_MESH_CALIBRATE

This creates the meshes for each object in the gcode

### EXCLUDE_OBJECT_START

This is added to the gcode by the slicer (or moonraker) when each of the objects starts printing. We hijack this and
load the mesh as part of it.

## Development

The macro content (ie. the gcode) is in `macros/${MACRO_NAME}.gcode`. Each macro has a corresponding `${MACRO_NAME}.vars.py`
 which contains default variables and other configuration that should appear in the rendered `[gcode_macro]` config block.

There is a test suite which is run on every pull request / push in GitHub Actions. This can be run locally.
Dependencies are managed with [poetry](https://python-poetry.org/): `pip install poetry`.

```bash
poetry install --with=dev
poetry run pytest tests/
```

To build the rendered config file:

```bash
make
```

The file is build to `output/adaptive_bed_mesh.cfg`.
