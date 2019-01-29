import json
import _thread
from flask import Blueprint

from app.config import TEAM_PROFILES, ORG_STRUCTURE
from app.daos.dao_team_metric import dao_get_sprints_between_daterange, dao_upsert_sprint
from app.daos.dao_git_metric import dao_get_git_metrics_between_daterange
from app.views import env
from app.source import get_quarter_daterange
from app.source.metrics import get_metrics

team_metrics_blueprint = Blueprint('/teams3/', __name__)

DUMMY_VIEWS = ['technology-operations', 'reliability-engineering', 'cyber']


@team_metrics_blueprint.route('/teams3/<path:path>/generate', methods=['GET'])
def teams_generate(path):
    for profile in TEAM_PROFILES:
        if profile['path'] == path:
            def generate_metrics():
                metrics = get_metrics(profile['source']['type'], profile['source']['id'], 2018, 3)

                for metric in metrics:
                    dao_upsert_sprint(metric)
                print(f'{profile["name"]} metrics generated')

                if profile['repos']:
                    get_metrics('github', profile['id'], year=2018, quarter=3)
                    print(f'{profile["name"]} git metrics generated')

            _thread.start_new_thread(generate_metrics, ())

            template = env.get_template('generating.html')
            team = {
                'name': profile['name'],
                'details': profile['description'],
                'has_subteams': 'false'
            }

            return template.render(team=team, breadcrumbs=_get_breadcrumbs(path), subteams=[])

    # team not found
    template = env.get_template('404.html')
    return template.render()


@team_metrics_blueprint.route('/teams3/<path:path>')
def teams(path):
    for profile in TEAM_PROFILES:
        if profile['path'] == path:
            metrics_list = []
            git_metrics = []

            q_start, q_end = get_quarter_daterange(2018, 3)

            for sprint in dao_get_sprints_between_daterange(profile['source']['id'], q_start, q_end):
                sprint_dict = sprint.serialize()
                sprint_dict, git_metrics = _get_git_metrics(profile, sprint_dict, git_metrics)
                metrics_list.append(sprint_dict)

            _check_repo_in_sprint(metrics_list, git_metrics)

            template = env.get_template('team-view.html')

            has_children = 'true' if _get_org_part(path).get('children') else 'false'

            team = {
                'name': profile['name'].capitalize(),
                'details': profile['description'],
                'has_subteams': has_children
            }

            return template.render(
                team=team,
                breadcrumbs=_get_breadcrumbs(path),
                subteams=_get_sub_teams(path),
                metrics=metrics_list,
                git_metrics=git_metrics
            )

    org_part = _get_org_part(path)
    if org_part and org_part['name'] in DUMMY_VIEWS:
        with open('data/dummy.json') as f:
            data = json.load(f)

        template = env.get_template('team-view.html')

        team = {
            'name': _get_nice_name(org_part['name']),
            'details': org_part['description'] if org_part.get('description') else org_part['name'].capitalize(),
            'has_subteams': 'true'
        }

        return template.render(
            team=team,
            breadcrumbs=_get_breadcrumbs(path),
            subteams=_get_sub_teams(path),
            metrics=data
        )

    template = env.get_template('404.html')
    return template.render()


def _get_org_part(path, structure=None, current_path=''):
    if not structure:
        structure = ORG_STRUCTURE

    children = []
    for part in structure:
        if f"{current_path}{part['name']}" == path:
            part['path'] = f"{current_path}{part['name']}"
            return part
        elif part.get('children'):
            children.append((part['children'], f"{part['name'].lower()}/"))

    for child, name in children:
        part = _get_org_part(path, child, f"{current_path}{name}")
        if part:
            return part

    return None


def _get_org_path(name, structure=None, current_path=''):
    if not structure:
        structure = ORG_STRUCTURE

    children = []
    for part in structure:
        if part['name'] == name:
            return f"{current_path}{part['name']}"
        elif part.get('children'):
            children.append((part['children'], f"{part['name'].lower()}/"))

    for child, _name in children:
        path = _get_org_path(name, child, f"{current_path}{_name}")
        if path:
            return path

    return None


def _get_nice_name(name):
    if name == 'gds':
        return 'GDS'

    nice_name = ''
    for word in name.split('-'):
        nice_name += word.capitalize() + ' '

    return nice_name


def _get_breadcrumbs(path):
    breadcrumbs = []
    valid = False
    for part in path.split("/"):
        link = _get_org_path(part)
        if part in [p['name'] for p in TEAM_PROFILES] or part in DUMMY_VIEWS:
            valid = True

        breadcrumbs.append(
            {
                'link': '/teams3/{}'.format(link) if valid else '#',
                'name': _get_nice_name(part)
            }
        )

    return breadcrumbs


def _get_sub_teams(path):
    subteams = []

    org_part = _get_org_part(path)

    if org_part.get('children'):
        for child in org_part.get('children'):
            subteam = {
                'name': child['description'] if child.get('description') else _get_nice_name(child['name']),
                'has_subteams': True if child.get('children') else False,
                'link': '/teams3/{}'.format(child['path']) if child.get('path') else '#'
            }

            for profile in TEAM_PROFILES:
                if profile['name'] == child['name']:
                    subteam['link'] = '/teams3/{}'.format(profile['path'])

            for dummy in DUMMY_VIEWS:
                if dummy == child['name']:
                    subteam['link'] = '/teams3/{}'.format(_get_org_path(child['name']))

            subteams.append(subteam)

    return subteams


def _get_git_metrics(profile, sprint, git_metrics):
    diff_count = total_diff_count = 0
    repos = []

    for gm in dao_get_git_metrics_between_daterange(str(profile['id']), sprint['started_on'], sprint['ended_on']):
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
        repo['url'] = f"https://github.com/alphagov/{gm.name}/pulls?utf8=%E2%9C%93&q=is%3Apr+is%3Aclosed+merged%3A{sprint['started_on'].split(' ')[0]}..{sprint['ended_on'].split(' ')[0]}"

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
        git_metric_sprint['start'] = sprint['started_on']
        git_metric_sprint['num_prs'] = repo['num_prs']
        git_metric_sprint['code_rework'] = repo['code_rework']
        git_metric_sprint['total_comments'] = repo['total_comments']
        git_metric_sprint['url'] = f"https://github.com/alphagov/{repo['name']}/pulls?utf8=%E2%9C%93&q=merged%3A{sprint['started_on'].split(' ')[0]}..{sprint['ended_on'].split(' ')[0]}+is%3Apr+is%3Aclosed"

        git_metric['sprints'].append(git_metric_sprint)

    sprint['code_rework'] = (diff_count / total_diff_count) * 100 if total_diff_count else 0
    sprint['repos'] = repos

    return sprint, git_metrics


def _check_repo_in_sprint(sprints, git_metrics):
    # if a repo hasn't been worked on then set code_rework to '-'
    for metric in git_metrics:
        for team_metric in sprints:
            if team_metric['started_on'] not in [m['start'] for m in metric['sprints']]:
                git_metric_sprint = {}
                git_metric_sprint['start'] = team_metric['started_on']
                git_metric_sprint['code_rework'] = '-'
                metric['sprints'].append(git_metric_sprint)
                metric['sprints'] = sorted(metric['sprints'], key=lambda m: m['start'])
