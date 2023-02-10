{% set all_objects = printer.exclude_object.objects %}
{% set object_count = all_objects | length %}

{% set bed_mesh_min = printer.configfile.settings.bed_mesh.mesh_min %}
{% set bed_mesh_max = printer.configfile.settings.bed_mesh.mesh_max %}
{% set probe_count = printer.configfile.settings.bed_mesh.probe_count %}
{% set probe_count = probe_count if probe_count|length > 1 else probe_count * 2  %}
{% set max_probe_point_distance_x = ( bed_mesh_max[0] - bed_mesh_min[0] ) / (probe_count[0] - 1)  %}
{% set max_probe_point_distance_y = ( bed_mesh_max[1] - bed_mesh_min[1] ) / (probe_count[1] - 1)  %}

{% for mesh_name in created_mesh_names %}
    {% if (mesh_name != "") and (mesh_name in printer.bed_mesh.profiles) %}
        BED_MESH_PROFILE REMOVE={mesh_name}
    {% endif %}
{% endfor %}
SET_GCODE_VARIABLE MACRO=BED_MESH_CALIBRATE VARIABLE=created_mesh_names VALUE=[]

{% set _do_multi_mesh = True %} ; do multi-mesh by default
{% if not per_object_mesh_enable %} ; unless per-object-mesh is disabled in config
    {% if verbose %}
        { action_respond_info( "ABM: per-object-mesh is disabled" ) }
    {% endif %}
    {% set _do_multi_mesh = False %}
{% elif object_count == 0 %} ; or if there are no objects
    {% if verbose %}
        { action_respond_info( "ABM: no objects found" ) }
    {% endif %}
    {% set _do_multi_mesh = False %}
{% elif object_count > multi_mesh_max_objects %} ; or if there are too many objects
    {% if verbose %}
        { action_respond_info( "ABM: %s objects is greater than multi_mesh_max_objects (%s)" | format(object_count, multi_mesh_max_objects ) ) }
    {% endif %}
    {% set _do_multi_mesh = False %}
{% endif %} # TODO: use multi_mesh_min_width here

{% if probe_dock_enable == True %}
    {attach_macro}              ; Attach/deploy a probe if the probe is stored somewhere outside of the print area
{% endif %}

{% if led_enable == True %}
    {status_macro}              ; Set status LEDs
{% endif %}

{% if not _do_multi_mesh %}
    ; Don't create multiple meshes
    { action_respond_info( "ABM: Not creating individual object meshes" ) }
    {% set _created_meshes = ["default"] %}

    {% set all_points = printer.exclude_object.objects | map(attribute='polygon') | sum(start=[]) %}
    {% set x_min = all_points | map(attribute=0) | min | default(bed_mesh_min[0]) %}
    {% set y_min = all_points | map(attribute=1) | min | default(bed_mesh_min[1]) %}
    {% set x_max = all_points | map(attribute=0) | max | default(bed_mesh_max[0]) %}
    {% set y_max = all_points | map(attribute=1) | max | default(bed_mesh_max[1]) %}

    { action_respond_info("{} object points, clamping to bed mesh [{!r} {!r}]".format(
        all_points | count,
        bed_mesh_min,
        bed_mesh_max,
    )) }

    {% if fuzz_enable == True %}
        {% set fuzz_range = range(fuzz_min * 100 | int, fuzz_max * 100 | int + 1) %}
        {% set x_min = (bed_mesh_min[0] + fuzz_max, x_min) | max - (fuzz_range | random / 100.0) | float %}
        {% set y_min = (bed_mesh_min[1] + fuzz_max, y_min) | max - (fuzz_range | random / 100.0) | float %}
        {% set x_max = (bed_mesh_max[0] - fuzz_max, x_max) | min + (fuzz_range | random / 100.0) | float %}
        {% set y_max = (bed_mesh_max[1] - fuzz_max, y_max) | min + (fuzz_range | random / 100.0) | float %}
    {% else %}
        {% set x_min = [ bed_mesh_min[0], x_min ] | max | float %}
        {% set y_min = [ bed_mesh_min[1], y_min ] | max | float %}
        {% set x_max = [ bed_mesh_max[0], x_max ] | min | float %}
        {% set y_max = [ bed_mesh_max[1], y_max ] | min | float %}
    {% endif %}

    { action_respond_info("Object bounds, clamped to the bed_mesh: {!r}, {!r}".format(
        (x_min, y_min),
        (x_max, y_max),
    )) }

    {% set points_x = (((x_max - x_min) / max_probe_point_distance_x) | round(method='ceil') | int) + 1 %}
    {% set points_y = (((y_max - y_min) / max_probe_point_distance_y) | round(method='ceil') | int) + 1 %}

    {% if (([points_x, points_y]|max) > 6) %}
        {% set algorithm = "bicubic" %}
        {% set min_points = 4 %}
    {% else %}
        {% set algorithm = "lagrange" %}
        {% set min_points = 3 %}
    {% endif %}
    { action_respond_info( "Algorithm: {}".format(algorithm)) }

    {% set points_x = [points_x, min_points]|max  %}
    {% set points_y = [points_y, min_points]|max  %}
    { action_respond_info( "Points: x: {}, y: {}".format(points_x, points_y) ) }

    {% if printer.configfile.settings.bed_mesh.relative_reference_index is defined %}
        {% set ref_index = (points_x * points_y / 2) | int %}
        { action_respond_info( "Reference index: {}".format(ref_index) ) }
    {% else %}
        {% set ref_index = -1 %}
    {% endif %}

    _BED_MESH_CALIBRATE PROFILE=default MESH_MIN={'%0.3f' | format(x_min)},{'%0.3f' | format(y_min)} MESH_MAX={'%0.3f' | format(x_max)},{'%0.3f' | format(y_max)} ALGORITHM={algorithm} PROBE_COUNT={points_x},{points_y} RELATIVE_REFERENCE_INDEX={ref_index}

{% else %}
    ; Create multiple meshes
    {% set _created_meshes = [] %}
    {% for object in all_objects %}
        {% set _obj_name = object.name %}
        {% set _obj_mesh_name = "ABM_%s" | format(_obj_name) | upper %}

        ; get object min/max bounds from polygon
        {% set _obj_x_min = object.polygon | map(attribute=0) | min %}
        {% set _obj_y_min = object.polygon | map(attribute=1) | min %}
        {% set _obj_x_max = object.polygon | map(attribute=0) | max %}
        {% set _obj_y_max = object.polygon | map(attribute=1) | max %}

        {% if fuzz_enable %}
            ; add some fuzz to the mesh bounds, ranged by fuzz_min and fuzz_max, clamped to the bed_mesh
            {% set fuzz_range = range(fuzz_min * 100 | int, fuzz_max * 100 | int + 1) %}

            {% set _obj_x_mesh_min = (_obj_x_min, bed_mesh_min[0] + fuzz_max) | max - (fuzz_range | random / 100.0) | float %}
            {% set _obj_y_mesh_min = (_obj_y_min, bed_mesh_min[1] + fuzz_max) | max - (fuzz_range | random / 100.0) | float %}
            {% set _obj_x_mesh_max = (_obj_x_max, bed_mesh_max[0] - fuzz_max) | min + (fuzz_range | random / 100.0) | float %}
            {% set _obj_y_mesh_max = (_obj_y_max, bed_mesh_max[1] - fuzz_max) | min + (fuzz_range | random / 100.0) | float %}
        {% else %}
            ; otherwise, set mesh bounds to object bounds, clamped to the bed_mesh
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

        ; calculate the number of points to probe based on the max_probe_point_distance
        {% set _obj_mesh_points_x = (((_obj_x_mesh_max - _obj_x_mesh_min) / max_probe_point_distance_x) | round(method='ceil') | int) + 1 %}
        {% set _obj_mesh_points_y = (((_obj_y_mesh_max - _obj_y_mesh_min) / max_probe_point_distance_y) | round(method='ceil') | int) + 1 %}

        {% if (([_obj_mesh_points_x, _obj_mesh_points_y]|max) > 6) %}
            ; if the number of points is greater than 6, use bicubic interpolation
            {% set _obj_mesh_algorithm = "bicubic" %}
            {% set _min_points = 4 %}
        {% else %}
            ; otherwise, use lagrange interpolation
            {% set _obj_mesh_algorithm = "lagrange" %}
            {% set _min_points = 3 %}
        {% endif %}
        { action_respond_info( "Object '{}' | Algorithm: {}".format(_obj_name, _obj_mesh_algorithm)) }

        ; ensure the number of points is at least 3 or 4
        {% set _obj_mesh_points_x = [_obj_mesh_points_x, _min_points] | max  %}
        {% set _obj_mesh_points_y = [_obj_mesh_points_y, _min_points] | max  %}
        { action_respond_info( "Object '{}' | Points: x: {}, y: {}".format(_obj_name, _obj_mesh_points_x, _obj_mesh_points_y) ) }

        {% if printer.configfile.settings.bed_mesh.relative_reference_index is defined %}
            ; if relative_reference_index is enabled in config, set the reference index to the center of the mesh
            {% set _obj_mesh_ref_index = (_obj_mesh_points_x * _obj_mesh_points_y / 2) | int %}
            { action_respond_info( "Object '{}' | Reference index: {}".format(_obj_name, _obj_mesh_ref_index) ) }
        {% else %}
            ; otherwise set the reference index to -1 (disabled)
            {% set _obj_mesh_ref_index = -1 %}
        {% endif %}

        ; call the firmware BED_MESH_CALIBRATE command for this object with the parameters we just calculated
        _BED_MESH_CALIBRATE PROFILE={_obj_mesh_name} MESH_MIN={'%0.3f' | format(_obj_x_mesh_min)},{'%0.3f' | format(_obj_y_mesh_min)} MESH_MAX={'%0.3f' | format(_obj_x_mesh_max)},{'%0.3f' | format(_obj_y_mesh_max)} ALGORITHM={_obj_mesh_algorithm} PROBE_COUNT={_obj_mesh_points_x},{_obj_mesh_points_y} RELATIVE_REFERENCE_INDEX={_obj_mesh_ref_index}

        {% set _ = _created_meshes.append(_obj_mesh_name) %}
    {% endfor %}

    ; Ensure we start the print with no mesh loaded
    BED_MESH_CLEAR

{% endif %}

; Set the created_mesh_names variable to a list of the mesh names we created
SET_GCODE_VARIABLE MACRO=BED_MESH_CALIBRATE VARIABLE=created_mesh_names VALUE='[{%- for mesh_name in _created_meshes %}"{ mesh_name }"{% if not loop.last %}, {% endif %}{% endfor %}]'

{% if probe_dock_enable == True %}
    {detach_macro}              ; Detach/stow a probe if the probe is stored somewhere outside of the print area
{% endif %}
