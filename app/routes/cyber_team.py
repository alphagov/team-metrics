import json
from flask import Blueprint

from app.routes import env, cyber_breadcrumbs

cyber_team_blueprint = Blueprint('/teams/gds/delivery-and-support/technology-operations/cyber', __name__)


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
    from app.daos.dao_team_metric import dao_get_sprints_project
    metrics_json = []
    for metric in dao_get_sprints_project('CT'):
        metrics_json.append(metric.serialize())

    # with open('data/CT.json') as f:
    #     data = json.load(f)

    template = env.get_template('team-view.html')
    team = {'name': 'Tooling', 'details': 'something something Cyber Tooling', 'has_subteams': 'false' }
    breadcrumbs = cyber_breadcrumbs.copy()
    breadcrumbs.append({ 'link': '/teams/gds/delivery-and-support/technology-operations/cyber/tooling', 'name': team['name'] })
    return template.render(team=team, breadcrumbs=breadcrumbs, subteams=[], metrics=metrics_json)


@cyber_team_blueprint.route('/teams/gds/delivery-and-support/technology-operations/cyber/tooling/generate', methods=['GET'])
def cyber_tooling_team_generate():
    import _thread

    def generate_metrics():
        from app.source.jira import Jira
        from app.daos.dao_team_metric import dao_add_sprint
        jira = Jira('CT')
        metrics = jira.get_metrics(last_num_weeks=12)
        for metric in metrics:
            dao_add_sprint(metric)
        print('CT metrics generated')

    _thread.start_new_thread(generate_metrics, ())

    template = env.get_template('generating.html')
    team = {'name': 'Tooling', 'details': 'something something Cyber Tooling', 'has_subteams': 'false' }
    breadcrumbs = cyber_breadcrumbs.copy()
    breadcrumbs.append({ 'link': '/teams/gds/delivery-and-support/technology-operations/cyber/tooling', 'name': team['name'] })
    return template.render(team=team, breadcrumbs=breadcrumbs, subteams=[])
