#!/usr/bin/env python

size = (95, 95)
spacing = 10
x_count = 3
y_count = 3

create_cmds = []

start_end_cmds = []

for y in range(y_count):
    for x in range(x_count):
        min_x = float(x * size[0] + spacing)
        min_y = float(y * size[1] + spacing)
        max_x = float(min_x + size[0])
        max_y = float(min_y + size[1])
        center = [str(min_x + size[0] / 2), str(min_y + size[1] / 2)]

        create_cmds.append(
            f"EXCLUDE_OBJECT_DEFINE NAME=object_{x}_{y} CENTER={','.join(center)} POLYGON=[[{min_x},{min_y}],[{max_x},{min_y}],[{max_x},{max_y}],[{min_x},{max_y}]]"
        )
        start_end_cmds.append(f"EXCLUDE_OBJECT_START NAME=object_{x}_{y}")
        start_end_cmds.append(f"EXCLUDE_OBJECT_END NAME=object_{x}_{y}")


print("\n".join(create_cmds))
print("\n\nM117\nPER_OBJECT_MESH\n")

print("\n".join(start_end_cmds))
