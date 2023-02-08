# Klipper Adaptive Bed Mesh (mesh-per-object)

## THIS IS VERY WIP

Basically, create a bed mesh for every object on the board, then load that mesh
when printing that object.

## Macros

### BED_MESH_CALIBRATE

This creates the meshes for each object in the gcode

### EXCLUDE_OBJECT_START

This is added to the gcode by the slicer (or moonraker) when each of the
objects starts printing. We hijack this and load the mesh as part of it.
