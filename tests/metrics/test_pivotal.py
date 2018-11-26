from datetime import datetime, timedelta
import pytest

from app.metrics import get_datetime, get_process_cycle_efficiency
from app.metrics.pivotal import Pivotal


def mock_pivotal_client(
    mocker, start="2018-11-01T12:00:00Z", finish="2018-11-14T12:00:00Z",
    stories=[], story_blockers=[], story_started="2018-11-01T12:00:00Z"
):
    mocker.patch("os.environ", {
        'TM_PIVOTAL_PAT': 'test_pat',
        'TM_PIVOTAL_PROJECT_ID': 'test_project_id',
    })

    if stories == []:
        stories = [
            {
                "id": 1,
                "current_state": "accepted",
                "name": "test",
                "accepted_at": "2018-11-03T12:00:00Z",
            }
        ]

    class MockPivotalClient:
        def __init__(self, _, project_id=''):
            pass

        def get_project_iterations(self):
            return [
                {
                    "start": "2018-11-01T12:00:00Z",
                    "finish": "2018-11-14T12:00:00Z",
                    "stories": stories
                }
            ]

        def get_story_blockers(self, story_id):
            for blocker in story_blockers:
                if blocker['story_id'] == story_id:
                    return story_blockers

            return []

        def get_story_activities(self, story_id):
            return [
                {
                    'highlight': 'started',
                    'changes': [
                        {
                            'new_values': {
                                'updated_at': "2018-11-01T12:00:00Z"
                            }
                        }
                    ]
                }
            ]

    mocker.patch("app.metrics.pivotal.PivotalClient", MockPivotalClient)


def test_get_blocked_time(mocker):
    story = {
            "id": 1,
            "current_state": "accepted",
            "name": "test",
            "created_at": "2018-11-01T12:00:00Z",
            "accepted_at": "2018-11-02T12:00:00Z",
    }

    story_blockers = [
        {
            'story_id': 1,
            'resolved': True,
            'created_at': '2018-11-01T12:00:00Z',
            'updated_at': '2018-11-02T12:00:00Z',
        }
    ]

    mock_pivotal_client(mocker, stories=[story], story_blockers=story_blockers)

    p = Pivotal()
    blocked_time = p.get_blocked_time(story['id'])
    assert blocked_time == timedelta(days=1)


def test_get_blocked_time_unresolved_is_none(mocker):
    story = {
            "id": 1,
            "current_state": "started",
            "name": "test",
            "created_at": "2018-11-01T12:00:00Z",
    }

    story_blockers = [
        {
            'story_id': 1,
            'resolved': False,
            'created_at': '2018-11-01T12:00:00Z',
            'updated_at': '2018-11-02T12:00:00Z',
        }
    ]

    mock_pivotal_client(mocker, stories=[story], story_blockers=story_blockers)

    p = Pivotal()
    blocked_time = p.get_blocked_time(story)
    assert blocked_time is None


def test_get_metrics(mocker):
    iteration_start = "2018-11-01T12:00:00Z"
    iteration_finish = "2018-11-14T12:00:00Z"
    story_started = "2018-11-01T12:00:00Z"
    story_accepted = "2018-11-03T12:00:00Z"
    story = {
        "id": 1,
        "current_state": "accepted",
        "name": "test",
        "accepted_at": story_accepted,
    }

    mock_pivotal_client(mocker, start=iteration_start, finish=iteration_finish, stories=[story])
    mock_write_csv_line = mocker.patch("app.metrics.pivotal.write_csv_line")

    p = Pivotal()
    metrics = p.get_metrics()

    assert len(metrics) == 1
    assert metrics[0].started_on == iteration_start
    assert metrics[0].ended_on == iteration_finish
    assert metrics[0].cycle_time == get_datetime(story_accepted) - get_datetime(story_started)
    assert metrics[0].process_cycle_efficiency == 1
    assert mock_write_csv_line.called


def test_get_metrics_with_story_blocker(mocker):
    iteration_start = "2018-11-01T12:00:00Z"
    iteration_finish = "2018-11-14T12:00:00Z"
    story_started = "2018-11-01T12:00:00Z"
    story_accepted = "2018-11-03T12:00:00Z"
    blocked_start = "2018-11-01T12:00:00Z"
    blocked_updated = "2018-11-02T12:00:00Z"

    story = {
        "id": 1,
        "current_state": "accepted",
        "name": "test",
        "accepted_at": story_accepted,
    }
    blocker = {
        "story_id": 1,
        "resolved": True,
        "created_at": blocked_start,
        "updated_at": blocked_updated,
    }

    mock_pivotal_client(
        mocker, start=iteration_start, finish=iteration_finish,
        stories=[story], story_blockers=[blocker]
    )
    mock_write_csv_line = mocker.patch("app.metrics.pivotal.write_csv_line")

    p = Pivotal()
    metrics = p.get_metrics()

    assert len(metrics) == 1
    assert metrics[0].started_on == "2018-11-01T12:00:00Z"
    assert metrics[0].ended_on == "2018-11-14T12:00:00Z"
    assert metrics[0].cycle_time == get_datetime(story_accepted) - get_datetime(story_started)
    assert metrics[0].process_cycle_efficiency == (
        (get_datetime(blocked_updated) - get_datetime(blocked_start)) / metrics[0].cycle_time
    )
    assert metrics[0].num_incomplete == 0
    assert mock_write_csv_line.called


def test_get_metrics_with_story_blocker_unresolved(mocker):
    iteration_start = "2018-11-01T12:00:00Z"
    iteration_finish = "2018-11-14T12:00:00Z"
    story_started = "2018-11-01T12:00:00Z"
    story_accepted = "2018-11-03T12:00:00Z"
    blocked_start = "2018-11-01T12:00:00Z"

    stories = [
        {
            "id": 1,
            "current_state": "accepted",
            "name": "test",
            "accepted_at": story_accepted,
        },
        {
            "id": 2,
            "current_state": "started",
            "name": "test 2",
        }
    ]
    blocker = {
        "story_id": 2,
        "resolved": False,
        "created_at": blocked_start,
    }

    mock_pivotal_client(
        mocker, start=iteration_start, finish=iteration_finish,
        stories=stories, story_blockers=[blocker]
    )
    mock_write_csv_line = mocker.patch("app.metrics.pivotal.write_csv_line")

    p = Pivotal()
    metrics = p.get_metrics()

    assert len(metrics) == 1
    assert metrics[0].started_on == "2018-11-01T12:00:00Z"
    assert metrics[0].ended_on == "2018-11-14T12:00:00Z"
    assert metrics[0].cycle_time == get_datetime(story_accepted) - get_datetime(story_started)
    assert metrics[0].process_cycle_efficiency == 1
    assert metrics[0].num_incomplete == 1
    assert mock_write_csv_line.called
