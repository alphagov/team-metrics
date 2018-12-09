from team_metrics import Metrics
from team_metrics.daos.dao_team_metric import dao_get_sprints, dao_add_sprint


def test_dao_get_sprints(dbsession):
    m1 = Metrics(
        '1',
        1,
        '2018-11-01T12:00',
        '2018-11-08T12:00',
        'jira',
        '1 day',
        1,
        1,
        0
    )
    m2 = Metrics(
        '1',
        2,
        '2018-11-09T12:00',
        '2018-11-16T12:00',
        'jira',
        '1 day',
        1,
        1,
        0
    )
    dao_add_sprint(m1)
    dao_add_sprint(m2)
    sprints = dao_get_sprints()
    assert len(sprints) == 2


def test_add_sprint(dbsession):
    m = Metrics(
        '1',
        1,
        '2018-11-01T12:00',
        '2018-11-08T12:00',
        'jira',
        '1 day',
        1,
        1,
        0
    )
    dao_add_sprint(m)
    sprints = dao_get_sprints()
    assert len(sprints) == 1
