{% if printer["gcode_macro BED_MESH_CALIBRATE"].created_mesh_names == ["default"] %}
    ; if we only have the default mesh, we don't need to clear it
{% elif printer["gcode_macro BED_MESH_CALIBRATE"].created_mesh_names | length == 0 %}
    ; if we created no meshes, we don't need to clear anything
{% else %}
    BED_MESH_CLEAR
    {% if printer["gcode_macro BED_MESH_CALIBRATE"].verbose %}
        { action_respond_info("ABM: mesh cleared") }
    {% endif %}
{% endif %}

_EXCLUDE_OBJECT_END {rawparams}
