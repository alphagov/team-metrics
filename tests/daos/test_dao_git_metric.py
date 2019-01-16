from app.models import GitMetric
from app.daos.dao_git_metric import (
    dao_get_git_metrics,
    dao_get_git_metrics_between_daterange,
    dao_upsert_git_metric
)


def test_dao_get_git_metrics(dbsession):
    m1 = {
        'team_id': 'fake_team_id',
        'team_name': 'fake_team_name',
        'name': 'repo_name',
        'pr_number': '4',
        'start_date': '2018-11-09T12:00',
        'end_date': '2018-11-16T12:00',
        'diff_count': 90,
        'total_diff_count': 100,
        'comments_count': 5,
    }

    dao_upsert_git_metric(m1)
    metrics = dao_get_git_metrics()
    assert len(metrics) == 1


def test_dao_get_git_metric_between_narrow_daterange(sample_git_metrics):
    metrics = dao_get_git_metrics_between_daterange(sample_git_metrics[0]['team_id'], '2018-11-17T12:00', '2018-11-18T12:00')
    assert len(metrics) == 1


def test_dao_get_git_metric_between_wider_daterange(sample_git_metrics):
    metrics = dao_get_git_metrics_between_daterange(sample_git_metrics[0]['team_id'], '2018-11-08T12:00', '2018-11-19T12:00')
    assert len(metrics) == 2


def test_dao_get_git_metric_between_wider_daterange_midweek(sample_git_metrics):
    git_metrics = dao_get_git_metrics_between_daterange(sample_git_metrics[0]['team_id'], '2018-11-01T12:00', '2018-11-21T12:00')
    assert len(git_metrics) == 2


def test_upsert_git_metric_can_add_metric(dbsession):
    m = {
            'team_id': 'fake_team_id',
            'team_name': 'fake_team_name',
            'name': 'repo_name',
            'pr_number': '4',
            'start_date': '2018-11-09T12:00',
            'end_date': '2018-11-16T12:00',
            'diff_count': 90,
            'total_diff_count': 100,
            'comments_count': 5,
        }
    dao_upsert_git_metric(m)
    db_metrics = dbsession.query(GitMetric).all()

    assert len(db_metrics) == 1
    assert db_metrics[0].team_id == m['team_id']
    assert db_metrics[0].name == m['name']


def test_upsert_git_metric_can_update_metric(dbsession):
    m = {
            'team_id': 'fake_team_id',
            'team_name': 'fake_team_name',
            'name': 'repo_name',
            'pr_number': '4',
            'start_date': '2018-11-09T12:00',
            'end_date': '2018-11-16T12:00',
            'diff_count': 90,
            'total_diff_count': 100,
            'comments_count': 5,
        }
    dao_upsert_git_metric(m)
    db_metrics = dbsession.query(GitMetric).all()

    assert len(db_metrics) == 1

    m['total_diff_count'] = 110

    dao_upsert_git_metric(m)

    db_metrics = dbsession.query(GitMetric).all()

    assert len(db_metrics) == 1
    assert db_metrics[0].total_diff_count == m['total_diff_count']
