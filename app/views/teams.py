import json
import _thread
from flask import Blueprint, current_app

from app.config import TEAM_PROFILES
from app.daos.dao_team_metric import dao_get_sprints_between_daterange, dao_upsert_sprint
from app.daos.dao_git_metric import dao_get_git_metrics_between_daterange, dao_upsert_git_metric
from app.views import env
from app.source import get_quarter_daterange
from app.source.metrics import get_metrics

base_breadcrumbs = [
    { 'link': '#', 'name': 'GDS' },
    { 'link': '#', 'name': 'Delivery & Support' },
]

STRUCTURE = [
    {
        'name': 'technology-operations',
        'description': 'Tech ops',
        'path': 'gds/delivery-and-support/technology-operations',
        'children': [
            {
                'name': 'reliability-engineering',
                'description': 'Reliability Engineering',
                'path': 'gds/delivery-and-support/technology-operations/reliability-engineering',
                'children': [
                    {
                        'name': 'build-run',
                        'description': 'New Platform - Build / Run',
                        'path': '#',
                    },
                    {
                        'name': 'observe',
                        'description': 'New Platform - Observe',
                        'path': '#',
                    },
                    {
                        'name': 'paas',
                        'description': 'GOV.UK PaaS',
                        'path': '#',
                    },
                    {
                        'name': 'govuk-migration',
                        'description': 'Gov.UK Migration',
                        'path': '#',
                    },
                    {
                        'name': 'automate',
                        'description': 'Automate',
                        'path': '#',
                    },
                ]
            },
            {
                'name': 'user-support',
                'description': 'User Support',
                'path': '#',
            },
            {
                'name': 'cyber-security',
                'description': 'Cyber Security',
                'path': 'gds/delivery-and-support/technology-operations/cyber',
                'children': [
                    {
                        'name': 'engage',
                        'description': 'Engage',
                        'path': '#',
                    },
                    {
                        'name': 'tooling',
                        'description': 'Tooling',
                        'path': '#',
                    },
                    {
                        'name': 'operational-intelligence',
                        'description': 'Operational intelligence',
                        'path': '#',
                    },
                    {
                        'name': 'consult',
                        'description': 'Consult',
                        'path': '#',
                    },
                ]
            },
            {
                'name': 'traceability',
                'description': 'Traceability',
                'path': '#',
            }
        ]
    },
]

teams_blueprint = Blueprint('/teams2/', __name__)


@teams_blueprint.route('/teams2/<path:path>')
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

            has_children = 'true' if _get_children(profile['name'], STRUCTURE) else 'false'

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

    dummy_view = _get_dummy_view(path, STRUCTURE)
    if dummy_view:
        return dummy_view

    template = env.get_template('404.html')
    return template.render()


def _get_dummy_view(path, dummy_views):
    children = []
    for dummy_page in dummy_views:
        if dummy_page['path'] == path:
            with open('data/dummy.json') as f:
                data = json.load(f)

            template = env.get_template('team-view.html')

            team = {
                'name': _get_nice_names(dummy_page['name']),
                'details': dummy_page['description'],
                'has_subteams': 'true'
            }

            return template.render(
                team=team,
                breadcrumbs=_get_breadcrumbs(path),
                subteams=_get_sub_teams(path),
                metrics=data
            )
        elif dummy_page.get('children'):
            children.append(dummy_page['children'])

    for child in children:
        return _get_dummy_view(path, child)


def _get_dummy_link(name, dummy_views):
    children = []
    for dummy_page in dummy_views:
        if dummy_page['name'] == name:
            return dummy_page['path']
        elif dummy_page.get('children'):
            children.append(dummy_page['children'])

    for child in children:
        return _get_dummy_link(name, child)


def _get_children(name, structure):
    children = []
    for part in structure:
        if part['name'] == name:
            return part.get('children', [])
        elif part.get('children'):
            children.append(part['children'])

    for child in children:
        return _get_children(name, child)


def _get_nice_names(name):
    if name == 'gds':
        return 'GDS'

    nice_name = ''
    for word in name.split('-'):
        nice_name += word.capitalize() + ' '

    return nice_name


def _get_breadcrumbs(path):
    breadcrumbs = []

    for part in path.split("/"):
        link = _get_dummy_link(part, STRUCTURE)
        breadcrumbs.append(
            {
                'link': '/teams2/{}'.format(link) if link else '#',
                'name': _get_nice_names(part)
            }
        )

    # breadcrumbs[-1]['link'] = f'teams/{path}'

    return breadcrumbs


def _get_sub_teams(path):
    subteams = []

    current_page = path.split("/")[-1]

    children = _get_children(current_page, STRUCTURE)

    if children:
        for child in children:
            subteam = {
                'name': _get_nice_names(child['name']),
                'has_subteams': 'true' if child.get('children') else 'false',
                'link': '/teams2/{}'.format(child['path']) if child['path'] != '#' else '#'
            }

            for profile in TEAM_PROFILES:
                if profile['name'] == child['name']:
                    subteam['link'] = '/teams2/{}'.format(profile['path'])

            subteams.append(subteam)

    return subteams


def _get_git_metrics(profile, sprint, git_metrics):
    diff_count = total_diff_count = 0
    repos = []

    for gm in dao_get_git_metrics_between_daterange(profile['id'], sprint['started_on'], sprint['ended_on']):
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
    # if a repo hasn't been worked on then set code_rework to -
    for metric in git_metrics:
        for team_metric in sprints:
            if team_metric['started_on'] not in [m['start'] for m in metric['sprints']]:
                git_metric_sprint = {}
                git_metric_sprint['start'] = team_metric['started_on']
                git_metric_sprint['code_rework'] = '-'
                metric['sprints'].append(git_metric_sprint)
                metric['sprints'] = sorted(metric['sprints'], key=lambda m: m['start'])


@teams_blueprint.route('/teams2/<path:path>/generate', methods=['GET'])
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
