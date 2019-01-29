from datetime import datetime, timedelta
import json

from flask import Blueprint
from app.config import get_team_profile
from app.daos.dao_team_metric import dao_get_sprints_between_daterange, dao_upsert_sprint
from app.daos.dao_git_metric import dao_get_git_metrics_between_daterange, dao_upsert_git_metric
from app.views import env, re_breadcrumbs
from app.source import get_quarter_daterange
from app.source.metrics import get_metrics

re_programme_blueprint = Blueprint('/teams/gds/delivery-and-support/technology-operations/reliability-engineering', __name__)

OBSERVE_TEAM_ID = '1'
PAAS_TEAM_ID = '2'


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
    team = get_team_profile(PAAS_TEAM_ID)

    metrics_json = []

    q_start, q_end = get_quarter_daterange(2018, 3)

    for metric in dao_get_sprints_between_daterange(team['source']['id'], q_start, q_end):
        metrics_json.append(metric.serialize())

    template = env.get_template('team-view.html')
    team = {'name': 'GOV.UK PaaS', 'details': 'something something GOV.UK PaaS', 'has_subteams': 'false' }
    breadcrumbs = re_breadcrumbs.copy()
    breadcrumbs.append({ 'link': '/teams/gds/delivery-and-support/technology-operations/reliability-engineering/paas', 'name': team['name'] })
    return template.render(team=team, breadcrumbs=breadcrumbs, subteams=[], metrics=metrics_json)


@re_programme_blueprint.route('/teams/gds/delivery-and-support/technology-operations/reliability-engineering/paas/generate', methods=['GET'])
def paas_team_generate():
    import _thread

    team_profile = get_team_profile(PAAS_TEAM_ID)

    def generate_metrics():
        metrics = get_metrics(team_profile['source']['type'], team_profile['source']['id'], 2018, 3)

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
    team = get_team_profile(OBSERVE_TEAM_ID)

    metrics_json = []
    git_metrics = []

    q_start, q_end = get_quarter_daterange(2018, 3)

    sprints = dao_get_sprints_between_daterange(team['source']['id'], q_start, q_end)

    for metric in sprints:
        team_metric = metric.serialize()

        diff_count = total_diff_count = 0
        repos = []

        for gm in dao_get_git_metrics_between_daterange(OBSERVE_TEAM_ID, team_metric['started_on'], team_metric['ended_on']):
            repo = [r for r in repos if r['name'] == gm.name]
            if repo:
                repo = repo[0]
            else:
                repo = {}
                repo['name'] = gm.name
                repo['num_prs'] = 0
                repo['diff_count'] = 0
                repo['total_diff_count'] = 0
                repo['total_comments'] = 0
                repos.append(repo)

            if gm.total_diff_count > 0:
                repo['diff_count'] += gm.diff_count
                repo['total_diff_count'] += gm.total_diff_count

                diff_count += gm.diff_count
                total_diff_count += gm.total_diff_count

            repo['num_prs'] += 1
            repo['total_comments'] += gm.comments_count
            repo['url'] = f"https://github.com/alphagov/{gm.name}/pulls?utf8=%E2%9C%93&q=is%3Apr+is%3Aclosed+merged%3A{team_metric['started_on'].split(' ')[0]}..{team_metric['ended_on'].split(' ')[0]}"

        for repo in repos:
            repo['code_rework'] = (repo['diff_count'] / repo['total_diff_count']) * 100

            _git_metrics = [g for g in git_metrics if g['name'] == repo['name']]
            if _git_metrics:
                git_metric = _git_metrics[0]
            else:
                git_metric = {}
                git_metric['name'] = repo['name']
                git_metric['sprints'] = []
                git_metrics.append(git_metric)

            git_metric_sprint = {}
            git_metric_sprint['start'] = team_metric['started_on']
            git_metric_sprint['num_prs'] = repo['num_prs']
            git_metric_sprint['code_rework'] = repo['code_rework']
            git_metric_sprint['total_comments'] = repo['total_comments']
            git_metric_sprint['url'] = f"https://github.com/alphagov/{repo['name']}/pulls?utf8=%E2%9C%93&q=merged%3A{team_metric['started_on'].split(' ')[0]}..{team_metric['ended_on'].split(' ')[0]}+is%3Apr+is%3Aclosed"

            git_metric['sprints'].append(git_metric_sprint)

        team_metric['code_rework'] = (diff_count / total_diff_count) * 100 if total_diff_count else 0
        team_metric['repos'] = repos
        metrics_json.append(team_metric)

    # if a repo hasn't been worked on then set code_rework to -
    for metric in git_metrics:
        for team_metric in sprints:
            if str(team_metric.started_on) not in [m['start'] for m in metric['sprints']]:
                git_metric_sprint = {}
                git_metric_sprint['start'] = str(team_metric.started_on)
                git_metric_sprint['code_rework'] = '-'
                metric['sprints'].append(git_metric_sprint)
                metric['sprints'] = sorted(metric['sprints'], key=lambda m: m['start'])

    template = env.get_template('team-view.html')
    team = {'name': 'Reliability Engineering - Observe', 'details': 'Prometheus, Grafana and Logit', 'has_subteams': 'false'}
    breadcrumbs = re_breadcrumbs.copy()
    breadcrumbs.append({'link': '/teams/gds/delivery-and-support/technology-operations/reliability-engineering/observe', 'name': team['name']})
    return template.render(team=team, breadcrumbs=breadcrumbs, subteams=[], metrics=metrics_json, git_metrics=git_metrics)


@re_programme_blueprint.route('/teams/gds/delivery-and-support/technology-operations/reliability-engineering/observe/generate', methods=['GET'])
def observe_team_generate():
    import _thread

    team_profile = get_team_profile(OBSERVE_TEAM_ID)

    def generate_metrics():
        from app.source.github import Github

        metrics = get_metrics(team_profile['source']['type'], team_profile['source']['id'], 2018, 3)
        for metric in metrics:
            dao_upsert_sprint(metric)
        print('Observe metrics generated')

        gh = Github(OBSERVE_TEAM_ID)
        gh.get_metrics(year=2018, quarter=3)
        print('Observe git metrics generated')

    _thread.start_new_thread(generate_metrics, ())

    template = env.get_template('generating.html')
    team = {'name': 'Reliability Engineering - Observe', 'details': 'Prometheus, Grafana and Logit', 'has_subteams': 'false' }
    breadcrumbs = re_breadcrumbs.copy()
    breadcrumbs.append({ 'link': '/teams/gds/delivery-and-support/technology-operations/reliability-engineering/observe', 'name': team['name'] })
    return template.render(team=team, breadcrumbs=breadcrumbs, subteams=[])
