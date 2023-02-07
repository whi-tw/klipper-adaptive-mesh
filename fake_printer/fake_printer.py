import os

import jinja2

from . import functions, models


class FakePrinter:
    template: jinja2.Template = None

    def __init__(self, tmpl_dir="."):
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(tmpl_dir),
            variable_start_string="{",
            variable_end_string="}",
            line_comment_prefix=";",
        )
        self.env.globals.update(action_respond_info=functions.action_respond_info)
        self.printer = models.Printer()

    def load_template(self, template_name):
        self.template = self.env.get_template(template_name)

    def render(self, *args, **kwargs):
        if "printer" in kwargs:
            raise ValueError("printer is a reserved keyword")
        result = self.template.render(*args, printer=self.printer, **kwargs)

        return os.linesep.join([s for s in result.splitlines() if s.strip()])
