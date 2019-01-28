from datetime import datetime, timedelta
import json
from flask import Blueprint

from app.config import TM_JIRA_PROJECT
from app.daos.dao_team_metric import dao_get_sprints_between_daterange, dao_upsert_sprint
from app.routes import env, cyber_breadcrumbs
from app.source import get_quarter_daterange, get_team_profile
from app.source.metrics import get_metrics

cyber_team_blueprint = Blueprint('/teams/gds/delivery-and-support/technology-operations/cyber', __name__)

CYBER_TOOLING_TEAM_ID = '3'


@cyber_team_blueprint.route('/teams/gds/delivery-and-support/technology-operations/cyber', methods=['GET'])
def cyber_team():
    with open('data/dummy.json') as f:
        data = json.load(f)

    template = env.get_template('team-view.html')
    team = {'name': 'Cyber', 'details': 'something something Cyber', 'has_subteams': 'true' }
    breadcrumbs = cyber_breadcrumbs.copy()
    subteams = [ { 'has_subteams': 'false', 'link': '#', 'name': 'Engage' },
                 { 'has_subteams': 'false', 'link': '/teams/gds/delivery-and-support/technology-operations/cyber/tooling', 'name': 'Tooling' },
                 { 'has_subteams': 'false', 'link': '#', 'name': 'Operational Intelligence' },
                 { 'has_subteams': 'false', 'link': '#', 'name': 'Consult' },
                 ]
    return template.render(team=team, breadcrumbs=breadcrumbs, subteams=subteams, metrics=data)


@cyber_team_blueprint.route('/teams/gds/delivery-and-support/technology-operations/cyber/tooling', methods=['GET'])
def cyber_tooling_team():
    metrics_json = []

    q_start, q_end = get_quarter_daterange(2018, 3)

    for metric in dao_get_sprints_between_daterange(TM_JIRA_PROJECT, q_start, q_end):
        metrics_json.append(metric.serialize())
    
    template = env.get_template('team-view.html')
    team = {'name': 'Tooling', 'details': 'something something Cyber Tooling', 'has_subteams': 'false' }
    breadcrumbs = cyber_breadcrumbs.copy()
    breadcrumbs.append({ 'link': '/teams/gds/delivery-and-support/technology-operations/cyber/tooling', 'name': team['name'] })
    return template.render(team=team, breadcrumbs=breadcrumbs, subteams=[], metrics=metrics_json)


@cyber_team_blueprint.route('/teams/gds/delivery-and-support/technology-operations/cyber/tooling/generate', methods=['GET'])
def cyber_tooling_team_generate():
    import _thread

    team_profile = get_team_profile(CYBER_TOOLING_TEAM_ID)

    def generate_metrics():
        metrics = get_metrics(team_profile['source']['type'], team_profile['source']['id'], 2018, 3)

        for metric in metrics:
            dao_upsert_sprint(metric)
        print('Cyber Tooling metrics generated')

    _thread.start_new_thread(generate_metrics, ())

    template = env.get_template('generating.html')
    team = {'name': 'Tooling', 'details': 'something something Cyber Tooling', 'has_subteams': 'false' }
    breadcrumbs = cyber_breadcrumbs.copy()
    breadcrumbs.append({ 'link': '/teams/gds/delivery-and-support/technology-operations/cyber/tooling', 'name': team['name'] })
    return template.render(team=team, breadcrumbs=breadcrumbs, subteams=[])
