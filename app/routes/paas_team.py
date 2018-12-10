import json

from flask import Blueprint
from app.routes import env, re_breadcrumbs

paas_team_blueprint = Blueprint('/teams/gds/delivery-and-support/technology-operations/reliability-engineering/paas', __name__)


@paas_team_blueprint.route('/teams/gds/delivery-and-support/technology-operations/reliability-engineering/paas', methods=['GET'])
def paas_team():
    with open('data/paas.json') as f:
        data = json.load(f)

    template = env.get_template('team-view.html')
    team = {'name': 'GOV.UK PaaS', 'details': 'something something GOV.UK PaaS', 'has_subteams': 'false' }
    breadcrumbs = re_breadcrumbs.copy()
    breadcrumbs.append({ 'link': '/teams/gds/delivery-and-support/technology-operations/reliability-engineering/paas', 'name': team['name'] })
    return template.render(team=team, breadcrumbs=breadcrumbs, subteams=[], metrics=data)
