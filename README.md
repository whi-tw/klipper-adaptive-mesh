# Klipper Adaptive Bed Mesh (mesh-per-object)

## ⚠️ Work in Progress - Not production-ready! ⚠️

## Description

> *TL;DR*: One bed mesh for each printed object

There are predominantly two major ways of doing bed meshes in Klipper:

1. Create one single mesh for the whole bed, using the settings in [the `[bed_mesh]` config section](https://www.klipper3d.org/Bed_Mesh.html).
2. Create a mesh for only the area used by the current print. There are multiple implementations of this, but the ones I have seen most commonly used are [kyleisah/Klipper-Adaptive-Meshing-Purging](https://github.com/kyleisah/Klipper-Adaptive-Meshing-Purging) and [Klipper mesh on print area only (ChipCE)](https://gist.github.com/ChipCE/95fdbd3c2f3a064397f9610f915f7d02)

With the knowledge of [`[exclude_object]`](https://www.klipper3d.org/Exclude_Object.html), I imagine a third kind of mesh generation, one where each object gets its own personal *small* mesh, for only the area on the build plate that it covers. This way, each object has as detailed a mesh as possible, hopefully increasing the precision.

## Table of Contents
<!-- START doctoc -->
<!-- END doctoc -->

## Setup

**Exclude Objects** must be configured. See the [Mainsail Docs](https://docs.mainsail.xyz/features/exclude_objects) for a good guide on getting this set up.

Download the config file (`adaptive_bed_mesh.cfg`) from the [latest release](https://github.com/whi-tw/klipper-adaptive-mesh/releases/) and add this to your printer. Make sure the file is included in `printer.cfg`.

### Configuration

At the top of the file, under `[gcode_macro BED_MESH_CALIBRATE]` there are some user-configurable variables. These are documented within the config file, and modify some behaviours of the macro. Ones you may wish to look at are:

<dl>
 <dt>`variable_fuzz_*`</dt>
 <dd>If using [voron-tap][https://github.com/VoronDesign/Voron-Tap] or similar (where the nozzle contacts the bed when probing), fuzz will reduce the likelihood of the same point being probed repeatedly, hopefully reducing possible damage to the bed.</dd>
 <dt>`variable_probe_dock_enable`</dt>
 <dd>If using a dockable probe ([klicky](https://github.com/jlas1/Klicky-Probe) etc.), this will allow you to call another macro before and after probing, to attach and detach the probe.</dd>
 <dt>`variable_per_object_mesh_enable`</dt>
 <dd>If this is set to `False`, per-object meshing will be disabled, and a single mesh that covers the extents of all the objects in the gcode file will be created.</dd>
 <dt>`variable_multi_mesh_max_objects`</dt>
 <dd>The threshold number of objects in the print job to create individual meshes for. If the number of objects exceeds this limit, one single mesh will be created that covers all of them.</dd>
 <dt>`variable_verbose`</dt>
 <dd>Enables verbose output from the macro. This is set to `True` by default while the macro is in development.</dd>
</dl>

## Macros Added

### BED_MESH_CALIBRATE

This hijacks the [built in command](https://www.klipper3d.org/G-Codes.html#bed_mesh_calibrate) (which is renamed to `_BED_MESH_CALIBRATE`) to create the individual meshes. This should be called with no parameters from your `PRINT_START` macro.

### EXCLUDE_OBJECT_START

This hijacks the [built in command](https://www.klipper3d.org/G-Codes.html#exclude_object_start) (which is renamed to `_EXCLUDE_OBJECT_START`).
`EXCLUDE_OBJECT_START` is added to the gcode by the slicer (or moonraker, I'm not 100% sure) just before an object starts printing on the current layer. We hijack this and load the object's mesh at this point, then call the original command.

## Caveats / gotchas

There are some caveats and potential gotchas here.

1. `BED_MESH_CALIBRATE` can take longer. If you're printing a large number of small objects (and `variable_multi_mesh_max_objects` is set to an equally large number), a large number of points may be probed, with some overlap. This is the reason that config option was created.  Equally, it can take much less time: a single 7x7 mesh has 49 points, while 3x 3x3 meshes have 27 points. Each point takes the same amount of time to probe, so (ignoring travel time) this macro can be faster
2. Skirt / brim can be printed without a mesh. I'm not 100% certain on this, as I haven't fully scrutinised a gcode file, but I suspect that these features may not be included as part of the object, and so may be printed outside of the `EXCLUDE_OBJECT_START` / `EXCLUDE_OBJECT_END` guards. Needs to be determined.

## Development

The macro content (ie. the gcode) is in `macros/${MACRO_NAME}.gcode`. Each macro has a corresponding `${MACRO_NAME}.vars.py` which contains default variables and other configuration that should appear in the rendered `[gcode_macro]` config block.

There is a test suite which is run on every pull request / push in GitHub Actions. This can be run locally. Dependencies are managed with [poetry](https://python-poetry.org/): `pip install poetry`.

```bash
poetry install --with=dev
poetry run pytest tests/
```

To build the rendered config file:

```bash
make
```

The file is built to `output/adaptive_bed_mesh.cfg`.
