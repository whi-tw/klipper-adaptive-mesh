#!/usr/bin/env python

import ast
import sys

value = sys.argv[1]

print(f"value: {value}")

try:
    literal = ast.literal_eval(value)
except ValueError:
    raise ValueError("Unable to parse '%s' as a literal" % (value,))

print(f"literal: {literal}")
print(f"type: {type(literal)}")
