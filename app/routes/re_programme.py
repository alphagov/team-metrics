from datetime import datetime, timedelta
import json

from flask import Blueprint
from app.config import TM_TRELLO_BOARD_ID, TM_PIVOTAL_PROJECT_ID
from app.daos.dao_team_metric import dao_get_sprints_between_daterange
from app.routes import env, re_breadcrumbs
from app.source import get_quarter_daterange

re_programme_blueprint = Blueprint('/teams/gds/delivery-and-support/technology-operations/reliability-engineering', __name__)


@re_programme_blueprint.route('/teams/gds/delivery-and-support/technology-operations/reliability-engineering', methods=['GET'])
def re_programme():
    with open('data/dummy.json') as f:
        data = json.load(f)

    template = env.get_template('team-view.html')
    team = {'name': 'Reliability Engineering', 'details': 'something something Reliability Engineering', 'has_subteams': 'true' }
    breadcrumbs = re_breadcrumbs.copy()
    subteams = [
        {'has_subteams': 'false', 'link': '#', 'name': 'New Platform - Build / Run'},
        {'has_subteams': 'false', 'link': '/teams/gds/delivery-and-support/technology-operations/reliability-engineering/observe', 'name': 'New Platform - Observe'},
        {'has_subteams': 'false', 'link': '/teams/gds/delivery-and-support/technology-operations/reliability-engineering/paas', 'name': 'GOV.UK PaaS'},
        {'has_subteams': 'false', 'link': '#', 'name': 'GOV.UK Migration'},
        {'has_subteams': 'false', 'link': '#', 'name': 'Automate'},
    ]
    return template.render(team=team, breadcrumbs=breadcrumbs, subteams=subteams, metrics=data)


@re_programme_blueprint.route('/teams/gds/delivery-and-support/technology-operations/reliability-engineering/paas', methods=['GET'])
def paas_team():
    metrics_json = []

    q_start, q_end = get_quarter_daterange(2018, 3)

    for metric in dao_get_sprints_between_daterange(TM_PIVOTAL_PROJECT_ID, q_start, q_end):
        metrics_json.append(metric.serialize())

    template = env.get_template('team-view.html')
    team = {'name': 'GOV.UK PaaS', 'details': 'something something GOV.UK PaaS', 'has_subteams': 'false' }
    breadcrumbs = re_breadcrumbs.copy()
    breadcrumbs.append({ 'link': '/teams/gds/delivery-and-support/technology-operations/reliability-engineering/paas', 'name': team['name'] })
    return template.render(team=team, breadcrumbs=breadcrumbs, subteams=[], metrics=metrics_json)


@re_programme_blueprint.route('/teams/gds/delivery-and-support/technology-operations/reliability-engineering/paas/generate', methods=['GET'])
def paas_team_generate():
    import _thread

    def generate_metrics():
        from app.source.pivotal import Pivotal
        from app.daos.dao_team_metric import dao_upsert_sprint
        pivotal = Pivotal('1275640')
        metrics = pivotal.get_metrics(last_num_weeks=12)
        for metric in metrics:
            dao_upsert_sprint(metric)
        print('PaaS metrics generated')

    _thread.start_new_thread(generate_metrics, ())

    template = env.get_template('generating.html')
    team = {'name': 'GOV.UK PaaS', 'details': 'something something GOV.UK PaaS', 'has_subteams': 'false' }
    breadcrumbs = re_breadcrumbs.copy()
    breadcrumbs.append({ 'link': '/teams/gds/delivery-and-support/technology-operations/reliability-engineering/paas', 'name': team['name'] })
    return template.render(team=team, breadcrumbs=breadcrumbs, subteams=[])


@re_programme_blueprint.route('/teams/gds/delivery-and-support/technology-operations/reliability-engineering/observe', methods=['GET'])
def observe_team():
    metrics_json = []

    q_start, q_end = get_quarter_daterange(2018, 3)

    for metric in dao_get_sprints_between_daterange(TM_TRELLO_BOARD_ID, q_start, q_end):
        metrics_json.append(metric.serialize())

    template = env.get_template('team-view.html')
    team = {'name': 'Reliability Engineering - Observe', 'details': 'Prometheus, Grafana and Logit', 'has_subteams': 'false' }
    breadcrumbs = re_breadcrumbs.copy()
    breadcrumbs.append({ 'link': '/teams/gds/delivery-and-support/technology-operations/reliability-engineering/observe', 'name': team['name'] })
    return template.render(team=team, breadcrumbs=breadcrumbs, subteams=[], metrics=metrics_json)


@re_programme_blueprint.route('/teams/gds/delivery-and-support/technology-operations/reliability-engineering/observe/generate', methods=['GET'])
def observe_team_generate():
    import _thread

    def generate_metrics():
        from app.source.trello import Trello
        from app.daos.dao_team_metric import dao_upsert_sprint
        trello = Trello(TM_TRELLO_BOARD_ID)
        metrics = trello.get_metrics(last_num_weeks=12)
        for metric in metrics:
            dao_upsert_sprint(metric)
        print('Observe metrics generated')

    _thread.start_new_thread(generate_metrics, ())

    template = env.get_template('generating.html')
    team = {'name': 'Reliability Engineering - Observe', 'details': 'Prometheus, Grafana and Logit', 'has_subteams': 'false' }
    breadcrumbs = re_breadcrumbs.copy()
    breadcrumbs.append({ 'link': '/teams/gds/delivery-and-support/technology-operations/reliability-engineering/observe', 'name': team['name'] })
    return template.render(team=team, breadcrumbs=breadcrumbs, subteams=[])
