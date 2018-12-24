from datetime import timedelta

from app.metrics import Metrics
from app.models import TeamMetric
from app.daos.dao_team_metric import (
    dao_get_sprints,
    dao_add_sprint,
    dao_get_sprints_started_from,
    dao_upsert_sprint
)


def test_dao_get_sprints(dbsession):
    m1 = Metrics(
        '1',
        1,
        '2018-11-01T12:00',
        '2018-11-08T12:00',
        'jira',
        timedelta(days=1),
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
        timedelta(days=1),
        1,
        1,
        0
    )
    dao_add_sprint(m1)
    dao_add_sprint(m2)
    sprints = dao_get_sprints()
    assert len(sprints) == 2


def test_dao_get_sprint_started_from(sample_metrics):
    sprints = dao_get_sprints_started_from(sample_metrics[0].project_id, '2018-11-01T12:00')
    assert len(sprints) == 2


def test_dao_get_sprint_started_from_returns_None_if_no_sprints(sample_metrics):
    sprints = dao_get_sprints_started_from(sample_metrics[0].project_id, '2018-12-01T12:00')
    assert len(sprints) == 0


def test_add_sprint(dbsession):
    m = Metrics(
        '1',
        1,
        '2018-11-01T12:00',
        '2018-11-08T12:00',
        'jira',
        timedelta(days=1),
        1,
        1,
        0
    )
    dao_add_sprint(m)
    sprints = dao_get_sprints()
    assert len(sprints) == 1


def test_upsert_sprint_can_add_metric(dbsession):
    m = Metrics(
        'upsert_id',
        1,
        '2018-11-01T12:00',
        '2018-11-08T12:00',
        'jira',
        timedelta(days=1),
        1,
        1,
        0
    )
    dao_upsert_sprint(m)
    db_metrics = dbsession.query(TeamMetric).all()

    assert len(db_metrics) == 1
    assert db_metrics[0].project_id == m.project_id
    assert db_metrics[0].sprint_id == m.sprint_id


def test_upsert_sprint_can_update_metric(dbsession):
    m = Metrics(
        'upsert_id',
        1,
        '2018-11-01T12:00',
        '2018-11-08T12:00',
        'jira',
        timedelta(days=1),
        1,
        1,
        0
    )
    dao_upsert_sprint(m)
    db_metrics = dbsession.query(TeamMetric).all()

    assert len(db_metrics) == 1

    m.num_completed = 2
    m.num_incomplete = 5

    dao_upsert_sprint(m)

    db_metrics = dbsession.query(TeamMetric).all()

    assert len(db_metrics) == 1
    assert db_metrics[0].num_completed == m.num_completed
    assert db_metrics[0].num_incomplete == m.num_incomplete
