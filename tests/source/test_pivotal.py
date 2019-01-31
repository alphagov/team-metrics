from datetime import datetime, timedelta
import pytest

from app.source import get_datetime, get_process_cycle_efficiency
from app.source.pivotal import Pivotal


def mock_pivotal_client(
    mocker, project_info={}, iterations=[],
    story_started="2018-11-01T12:00:00Z", stories=[],
    story_blockers=[], story_activities={}
):
    mocker.patch("os.environ", {
        'TM_PIVOTAL_PAT': 'test_pat',
        'TM_PIVOTAL_PROJECT_ID': 'test_project_id',
    })

    if project_info == {}:
        project_info = {
            'iteration_length': 1,
            'current_iteration_number': 3
        }

    if iterations == []:
        iterations = [
            {
                "number": "1",
                "start": "2018-11-01T12:00:00Z",
                "finish": "2018-11-15T12:00:00Z",
                "stories": stories
            }
        ]

        if stories == []:
            stories = [
                {
                    "id": 1,
                    "current_state": "accepted",
                    "name": "test",
                    "accepted_at": "2018-11-01T12:00:00Z",
                }
            ]

    if story_activities == {}:
        story_activities[1] = [
            {
                'highlight': 'started',
                'changes': [
                    {
                        'kind': 'story',
                        'new_values': {
                            'updated_at': story_started
                        }
                    }
                ],
            }
        ]

    class MockPivotalClient:
        def __init__(self, _, project_id=''):
            self.project_id = project_id

        def get_project(self):
            return project_info

        def get_project_iterations(self, offset=1, limit=10):
            return iterations

        def get_story_blockers(self, story_id):
            for blocker in story_blockers:
                if blocker['story_id'] == story_id:
                    return story_blockers

            return []

        def get_story_activities(self, story_id):
            return story_activities.get(story_id)

    mocker.patch("app.source.pivotal.PivotalClient", MockPivotalClient)


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


def test_pvotal_get_metrics(mocker):
    story_started = "2018-11-01T12:00:00Z"
    story_accepted = "2018-11-05T12:00:00Z"
    story = {
        "id": 1,
        "current_state": "accepted",
        "name": "test",
        "accepted_at": story_accepted,
    }

    mock_pivotal_client(mocker, story_started=story_started, stories=[story])

    p = Pivotal()
    metrics = p.get_metrics()

    assert len(metrics) == 1
    assert metrics[0].avg_cycle_time == (
        # subtract 2 days as there is a weekend between start end accepted
        get_datetime(story_accepted) - get_datetime(story_started) - timedelta(days=2)
    ).total_seconds()
    assert metrics[0].process_cycle_efficiency == 1


def test_get_pivotal_metrics_with_story_blocker(mocker):
    story_started = "2018-11-01T12:00:00Z"
    story_accepted = "2018-11-05T12:00:00Z"
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
        mocker,
        stories=[story], story_blockers=[blocker]
    )

    p = Pivotal()
    metrics = p.get_metrics()

    assert len(metrics) == 1
    assert metrics[0].avg_cycle_time == (
        get_datetime(story_accepted) - get_datetime(story_started) - timedelta(days=2)
    ).total_seconds()

    assert metrics[0].process_cycle_efficiency == (
        (get_datetime(blocked_updated) - get_datetime(blocked_start)) /
        (get_datetime(story_accepted) - get_datetime(story_started) - timedelta(days=2))
    )
    assert metrics[0].num_incomplete == 0


def test_get_pivotal_metrics_with_story_blocker_unresolved(mocker):
    story_started = "2018-11-01T12:00:00Z"
    story_accepted = "2018-11-07T12:00:00Z"
    blocked_start = "2018-11-05T12:00:00Z"

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
        mocker,
        story_started=story_started,
        stories=stories, story_blockers=[blocker]
    )

    p = Pivotal()
    metrics = p.get_metrics()

    assert len(metrics) == 1
    assert metrics[0].avg_cycle_time == (
        get_datetime(story_accepted) - get_datetime(story_started) - timedelta(days=2)
    ).total_seconds()
    assert metrics[0].process_cycle_efficiency == 1
    assert metrics[0].num_incomplete == 1
