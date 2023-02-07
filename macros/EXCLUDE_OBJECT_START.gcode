{% set mesh_name = "ABM_" + params.NAME %}
{% if mesh_name in printer.bed_mesh.profiles %}
    BED_MESH_PROFILE LOAD={mesh_name}
{% else if "default" in printer.bed_mesh.profiles %}
    BED_MESH_PROFILE LOAD=default
{% endif %}

EXCLUDE_OBJECT_START {rawparams}
