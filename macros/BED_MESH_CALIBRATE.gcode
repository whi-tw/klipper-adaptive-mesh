{% set all_objects = printer.exclude_object.objects %}

{% set bed_mesh_min = printer.configfile.settings.bed_mesh.mesh_min %}
{% set bed_mesh_max = printer.configfile.settings.bed_mesh.mesh_max %}
{% set probe_count = printer.configfile.settings.bed_mesh.probe_count %}
{% set probe_count = probe_count if probe_count|length > 1 else probe_count * 2  %}
{% set max_probe_point_distance_x = ( bed_mesh_max[0] - bed_mesh_min[0] ) / (probe_count[0] - 1)  %}
{% set max_probe_point_distance_y = ( bed_mesh_max[1] - bed_mesh_min[1] ) / (probe_count[1] - 1)  %}

{% set mesh_params = [] %}

{% for object in all_objects %}
    {% set _obj_name = "ABM_" + object.name %}

    {% set _obj_x_min = object.polygon | map(attribute=0) | min %}
    {% set _obj_y_min = object.polygon | map(attribute=1) | min %}
    {% set _obj_x_max = object.polygon | map(attribute=0) | max %}
    {% set _obj_y_max = object.polygon | map(attribute=1) | max %}

    {% if fuzz_enable %}
        {% set fuzz_range = range(fuzz_min * 100 | int, fuzz_max * 100 | int + 1) %}

        {% set _obj_x_mesh_min = (_obj_x_min, bed_mesh_min[0] + fuzz_max) | max - (fuzz_range | random / 100.0) | float %}
        {% set _obj_y_mesh_min = (_obj_y_min, bed_mesh_min[1] + fuzz_max) | max - (fuzz_range | random / 100.0) | float %}
        {% set _obj_x_mesh_max = (_obj_x_max, bed_mesh_max[0] - fuzz_max) | min + (fuzz_range | random / 100.0) | float %}
        {% set _obj_y_mesh_max = (_obj_y_max, bed_mesh_max[1] - fuzz_max) | min + (fuzz_range | random / 100.0) | float %}
    {% else %}
        {% set _obj_x_mesh_min = [_obj_x_min, bed_mesh_min[0]] | max | float %}
        {% set _obj_y_mesh_min = [_obj_y_min, bed_mesh_min[1]] | max | float %}
        {% set _obj_x_mesh_max = [_obj_x_max, bed_mesh_max[0]] | min | float %}
        {% set _obj_y_mesh_max = [_obj_y_max, bed_mesh_max[1]] | min | float %}
    {% endif %}

    { action_respond_info("Object '{}' | Object bounds, clamped to the bed_mesh: {!r}, {!r}".format(
        _obj_name,
        (_obj_x_mesh_min, _obj_y_mesh_min),
        (_obj_x_mesh_max, _obj_y_mesh_max),
    )) }

    {% set _obj_mesh_points_x = (((_obj_x_mesh_max - _obj_x_mesh_min) / max_probe_point_distance_x) | round(method='ceil') | int) + 1 %}
    {% set _obj_mesh_points_y = (((_obj_y_mesh_max - _obj_y_mesh_min) / max_probe_point_distance_y) | round(method='ceil') | int) + 1 %}

    {% if (([_obj_mesh_points_x, _obj_mesh_points_y]|max) > 6) %}
        {% set _obj_mesh_algorithm = "bicubic" %}
        {% set _min_points = 4 %}
    {% else %}
        {% set _obj_mesh_algorithm = "lagrange" %}
        {% set _min_points = 3 %}
    {% endif %}
    { action_respond_info( "Object '{}' | Algorithm: {}".format(_obj_name, _obj_mesh_algorithm)) }

    {% set _obj_mesh_points_x = [_obj_mesh_points_x, _min_points] | max  %}
    {% set _obj_mesh_points_y = [_obj_mesh_points_y, _min_points] | max  %}
    { action_respond_info( "Object '{}' | Points: x: {}, y: {}".format(_obj_name, _obj_mesh_points_x, _obj_mesh_points_y) ) }

    {% if printer.configfile.settings.bed_mesh.relative_reference_index is defined %}
        {% set _obj_mesh_ref_index = (_obj_mesh_points_x * _obj_mesh_points_y / 2) | int %}
        { action_respond_info( "Object '{}' | Reference index: {}".format(_obj_name, _obj_mesh_ref_index) ) }
    {% else %}
        {% set _obj_mesh_ref_index = -1 %}
    {% endif %}

    {% set _obj_mesh_params = dict({
        "name": _obj_name,
        "x_min": '%0.3f' | format(_obj_x_mesh_min),
        "x_max": '%0.3f' | format(_obj_x_mesh_max),
        "y_min": '%0.3f' | format(_obj_y_mesh_min),
        "y_max": '%0.3f' | format(_obj_y_mesh_max),
        "points_x": _obj_mesh_points_x,
        "points_y": _obj_mesh_points_y,
        "algorithm": _obj_mesh_algorithm,
        "ref_index": _obj_mesh_ref_index,
    }) %}

    {% set _ = mesh_params.append( _obj_mesh_params ) %}
{% endfor %}


{% for mesh_name in created_mesh_names.split(",") %}
    {% if mesh_name != "" %}
        BED_MESH_PROFILE DELETE={mesh_name}
    {% endif %}
{% endfor %}


{% for mesh in mesh_params %}
    _BED_MESH_CALIBRATE PROFILE={mesh.name} MESH_MIN={mesh.x_min},{mesh.y_min} MESH_MAX={mesh.x_max},{mesh.y_max} ALGORITHM={mesh.algorithm} PROBE_COUNT={mesh.points_x},{mesh.points_y} RELATIVE_REFERENCE_INDEX={mesh.ref_index}
{% endfor %}

SET_GCODE_VARIABLE MACRO=BED_MESH_CALIBRATE VARIABLE=create_mesh_names VALUE="{%- for mesh in mesh_params %}{mesh.name}{% if not loop.last %},{% endif %}{% endfor %}"
