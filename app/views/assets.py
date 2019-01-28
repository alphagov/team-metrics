# load assets directly from govuk-frontend package
# this is done instead of overriding the `static` directory in Flask()

from flask import Blueprint, send_from_directory

assets_blueprint = Blueprint('/assets/<path:filename>', __name__)


@assets_blueprint.route('/assets/<path:filename>')
def send_file(filename):
    return send_from_directory('../node_modules/govuk-frontend/assets/', filename)
