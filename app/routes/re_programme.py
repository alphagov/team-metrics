from datetime import datetime, timedelta
import json

from flask import Blueprint
from app.config import TM_TRELLO_BOARD_ID, TM_PIVOTAL_PROJECT_ID, TM_GITHUB_TEAM_ID
from app.daos.dao_team_metric import dao_get_sprints_between_daterange, dao_upsert_sprint
from app.daos.dao_git_metric import dao_get_git_metrics_between_daterange, dao_upsert_git_metric
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
        pivotal = Pivotal('1275640')
        metrics = pivotal.get_metrics(year=2018, quarter=3)
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
        team_metric = metric.serialize()

        diff_count = total_diff_count = 0
        repos = []

        for gm in dao_get_git_metrics_between_daterange(TM_GITHUB_TEAM_ID, team_metric['started_on'], team_metric['ended_on']):
            print(gm)
            if gm.total_diff_count > 0:
                repo = [r for r in repos if r['url'] == gm.repo_url]
                if repo:
                    print('found', gm.repo_url)
                    repo = repo[0]
                else:
                    print('not found', gm.repo_url)
                    repo = {}
                    repo['name'] = gm.repo_url.split('/')[-1]
                    repo['url'] = gm.repo_url
                    repo['diff_count'] = 0
                    repo['total_diff_count'] = 0
                    repos.append(repo)

                repo['diff_count'] += gm.diff_count
                repo['total_diff_count'] += gm.total_diff_count

                diff_count += gm.diff_count
                total_diff_count += gm.total_diff_count

        for repo in repos:
            repo['code_rework'] = (repo['diff_count'] / repo['total_diff_count']) * 100

        team_metric['code_rework'] = (diff_count / total_diff_count) * 100
        team_metric['repos'] = repos
        metrics_json.append(team_metric)

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
        trello = Trello(TM_TRELLO_BOARD_ID)
        metrics = trello.get_metrics(year=2018, quarter=3)
        for metric in metrics:
            dao_upsert_sprint(metric)
        print('Observe metrics generated')

    _thread.start_new_thread(generate_metrics, ())

    template = env.get_template('generating.html')
    team = {'name': 'Reliability Engineering - Observe', 'details': 'Prometheus, Grafana and Logit', 'has_subteams': 'false' }
    breadcrumbs = re_breadcrumbs.copy()
    breadcrumbs.append({ 'link': '/teams/gds/delivery-and-support/technology-operations/reliability-engineering/observe', 'name': team['name'] })
    return template.render(team=team, breadcrumbs=breadcrumbs, subteams=[])
