{% set mesh_name = "ABM_%s" | format(params.NAME) | upper %} ; the object name can come in as lowercase, which is not what we worked with to create the meshes
{% set current_mesh = printer.bed_mesh.profile_name %}

{% set mesh_to_load = "" %}
{% if mesh_name in printer.bed_mesh.profiles
    and mesh_name in printer["gcode_macro BED_MESH_CALIBRATE"].created_mesh_names
%} ; if the mesh exists and we created it, load it
    {% set mesh_to_load = mesh_name %}
{% elif "default" in printer.bed_mesh.profiles
    and "default" in printer["gcode_macro BED_MESH_CALIBRATE"].created_mesh_names
%} ; if the mesh does not exist, but a default mesh exists that we created, load it
    {% set mesh_to_load = "default" %}
{% else %} ; if the mesh does not exist and no default mesh exists, do nothing
    {% if printer["gcode_macro BED_MESH_CALIBRATE"].verbose %}
        { action_respond_info("ABM: no mesh loaded - mesh named '%s' or 'default' not found." | format(mesh_name)) }
    {% endif %}
{% endif %}

{% if mesh_to_load != "" %}
    {% if mesh_to_load != current_mesh %}
        BED_MESH_PROFILE LOAD={mesh_to_load}
        {% if printer["gcode_macro BED_MESH_CALIBRATE"].verbose %}
            { action_respond_info("ABM: loaded mesh: %s" | format(mesh_name) ) }
        {% endif %}
    {% endif %}
{% endif %}

_EXCLUDE_OBJECT_START {rawparams}
