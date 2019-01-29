from os import path

from jinja2 import select_autoescape, ChoiceLoader, FileSystemLoader, Environment


# from https://github.com/lfdebrux/govuk-frontend-python/blob/d3dd9f6cb689731753346746d2b5c7229f5293e2/govuk_frontend/templates.py#L12
class Environment2(Environment):
    def join_path(self, template, parent):
        """Enable the use of relative paths in template import statements"""
        return path.normpath(path.join(path.dirname(parent), template))


env = Environment2(loader=ChoiceLoader(
    [
        FileSystemLoader('templates/'),
        FileSystemLoader("node_modules/govuk-frontend/"),
        FileSystemLoader("node_modules/govuk-frontend/components/")
    ]),
    autoescape=select_autoescape(['html', 'xml']),
    extensions=[])
