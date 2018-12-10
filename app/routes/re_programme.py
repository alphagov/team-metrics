import json

from flask import Blueprint
from app.routes import env, re_breadcrumbs

re_programme_blueprint = Blueprint('/teams/gds/delivery-and-support/technology-operations/reliability-engineering', __name__)


@re_programme_blueprint.route('/teams/gds/delivery-and-support/technology-operations/reliability-engineering', methods=['GET'])
def re_programme():
    with open('data/dummy.json') as f:
        data = json.load(f)

    template = env.get_template('team-view.html')
    team = {'name': 'Reliability Engineering', 'details': 'something something Reliability Engineering', 'has_subteams': 'true' }
    breadcrumbs = re_breadcrumbs.copy()
    subteams = [ { 'has_subteams': 'false', 'link': '#', 'name': 'New Platform - Build' },
                 { 'has_subteams': 'false', 'link': '#', 'name': 'New Platform - Run' },
                 { 'has_subteams': 'false', 'link': '#', 'name': 'New Platform - Observe' },
                 { 'has_subteams': 'false', 'link': '/teams/gds/delivery-and-support/technology-operations/reliability-engineering/paas', 'name': 'GOV.UK PaaS' },
                 { 'has_subteams': 'false', 'link': '#', 'name': 'GOV.UK Migration' },
                 { 'has_subteams': 'false', 'link': '#', 'name': 'Automate' },
                 ]
    return template.render(team=team, breadcrumbs=breadcrumbs, subteams=subteams, metrics=data)
