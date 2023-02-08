{% set mesh_name = "ABM_%s" | format(params.NAME) | upper %} ; the object name can come in as lowercase, which is not what we worked with to create the meshes

{% if mesh_name in printer.bed_mesh.profiles
   and mesh_name in printer["gcode_macro BED_MESH_CALIBRATE"].created_mesh_names
%} ; if the mesh exists and we created it, load it
    BED_MESH_PROFILE LOAD={mesh_name}
    {% if printer["gcode_macro BED_MESH_CALIBRATE"].verbose %}
        { action_respond_info("ABM: loaded mesh: %s" | format(mesh_name) ) }
    {% endif %}
{% elif "default" in printer.bed_mesh.profiles
   and "default" in printer["gcode_macro BED_MESH_CALIBRATE"].created_mesh_names
%} ; if the mesh does not exist, but a default mesh exists that we created, load it
    BED_MESH_PROFILE LOAD=default
    {% if printer["gcode_macro BED_MESH_CALIBRATE"].verbose %}
        { action_respond_info("ABM: loaded mesh: default") }
    {% endif %}
{% else %} ; if the mesh does not exist and no default mesh exists, do nothing
    {% if printer["gcode_macro BED_MESH_CALIBRATE"].verbose %}
        { action_respond_info("ABM: no mesh loaded - mesh named '%s' or 'default' not found.") }
    {% endif %}
{% endif %}

_EXCLUDE_OBJECT_START {rawparams}
