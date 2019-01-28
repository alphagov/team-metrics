import json

from flask import Blueprint
from app.views import env, techops_breadcrumbs

techop_team_blueprint = Blueprint('/teams/gds/delivery-and-support/technology-operations', __name__)


@techop_team_blueprint.route('/teams/gds/delivery-and-support/technology-operations', methods=['GET'])
def techops_team():
    with open('data/dummy.json') as f:
        data = json.load(f)

    template = env.get_template('team-view.html')
    team = {'name': 'Technology Operations', 'details': 'something something Technology Operations', 'has_subteams': 'true' }
    breadcrumbs = techops_breadcrumbs.copy()
    subteams = [ { 'has_subteams': 'true', 'link': '/teams/gds/delivery-and-support/technology-operations/reliability-engineering', 'name': 'Reliability Engineering' },
                 { 'has_subteams': 'true', 'link': '#', 'name': 'User Support' },
                 { 'has_subteams': 'true', 'link': '/teams/gds/delivery-and-support/technology-operations/cyber', 'name': 'Cyber Security' },
                 { 'has_subteams': 'false', 'link': '/teams/gds/delivery-and-support/technology-operations/traceability', 'name': 'Traceability' },
                 { 'has_subteams': 'false', 'link': '#', 'name': 'TechOps Homepage' },
                 ]
    return template.render(team=team, breadcrumbs=breadcrumbs, subteams=subteams, metrics=data)
