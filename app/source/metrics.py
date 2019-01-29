from app.errors import NotFound
from app.source.github import Github
from app.source.jira import Jira
from app.source.pivotal import Pivotal
from app.source.trello import Trello


def get_metrics(source_type, _id, year, quarter):
    if source_type == 'jira':
        j = Jira(project_id=_id)
        return j.get_metrics(year, quarter)
    elif source_type == 'pivotal':
        p = Pivotal(project_id=_id)
        return p.get_metrics(year, quarter)
    elif source_type == 'trello':
        t = Trello(board_id=_id)
        return t.get_metrics(year, quarter)
    elif source_type == 'github':
        gh = Github(team_id=_id)
        return gh.get_metrics(year, quarter)
    else:
        raise NotFound(f"Source {source_type} not found")
