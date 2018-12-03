from datetime import datetime, timedelta
import pytest

from team_metrics.source import get_datetime, get_process_cycle_efficiency
from team_metrics.source.pivotal import Pivotal


def mock_pivotal_client(
    mocker, project_info={}, iterations=[], stories=[],
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
                "start": "2018-11-01T12:00:00Z",
                "finish": "2018-11-14T12:00:00Z",
                "stories": stories
            }
        ]

        if stories == []:
            stories = [
                {
                    "id": 1,
                    "current_state": "accepted",
                    "name": "test",
                    "accepted_at": "2018-11-03T12:00:00Z",
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
                            'updated_at': "2018-11-01T12:00:00Z"
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

    mocker.patch("team_metrics.source.pivotal.PivotalClient", MockPivotalClient)


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
    story_started = "2018-11-01T12:00:00Z"
    story_accepted = "2018-11-03T12:00:00Z"
    story = {
        "id": 1,
        "current_state": "accepted",
        "name": "test",
        "accepted_at": story_accepted,
    }

    mock_pivotal_client(mocker, stories=[story])

    p = Pivotal()
    metrics = p.get_metrics()

    assert len(metrics) == 1
    assert metrics[0].cycle_time == get_datetime(story_accepted) - get_datetime(story_started)
    assert metrics[0].process_cycle_efficiency == 1


def test_get_metrics_last_2_weeks(mocker):
    iterations = [
        {
            "number": 1,
            "start": "2018-11-01T12:00:00Z",
            "finish": "2018-11-8T12:00:00Z",
            "stories": [
                {
                    "id": 1,
                    "current_state": "accepted",
                    "name": "test",
                    "accepted_at": "2018-11-03T12:00:00Z",
                },
                {
                    "id": 2,
                    "current_state": "accepted",
                    "name": "test 2",
                    "accepted_at": "2018-11-05T12:00:00Z",
                },
            ]
        },
        {
            "number": 2,
            "start": "2018-11-08T12:00:00Z",
            "finish": "2018-11-15T12:00:00Z",
            "stories": [
                {
                    "id": 3,
                    "current_state": "accepted",
                    "name": "test",
                    "accepted_at": "2018-11-10T12:00:00Z",
                },
            ]
        },
    ]
    story_activities = {}
    story_activities[1] = [
        {
            'highlight': 'started',
            'changes': [
                {
                    'kind': 'story',
                    'new_values': {
                        'updated_at': "2018-11-01T12:00:00Z"
                    }
                }
            ],
        }
    ]
    story_activities[2] = [
        {
            'highlight': 'started',
            'changes': [
                {
                    'kind': 'story',
                    'new_values': {
                        'updated_at': "2018-11-02T12:00:00Z"
                    }
                }
            ],
        }
    ]
    story_activities[3] = [
        {
            'highlight': 'started',
            'changes': [
                {
                    'kind': 'story',
                    'new_values': {
                        'updated_at': "2018-11-09T12:00:00Z"
                    }
                }
            ],
        }
    ]

    mock_pivotal_client(mocker, iterations=iterations, story_activities=story_activities)

    p = Pivotal()
    metrics = p.get_metrics(last_num_weeks=2)

    assert len(metrics) == 2
    assert metrics[0].started_on == iterations[0]['start']
    assert metrics[0].ended_on == iterations[0]['finish']
    assert metrics[0].cycle_time == (
        get_datetime(iterations[0]['stories'][0]['accepted_at']) -
        get_datetime(story_activities[1][0]['changes'][0]['new_values']['updated_at'])
    ) + (
        get_datetime(iterations[0]['stories'][1]['accepted_at']) -
        get_datetime(story_activities[2][0]['changes'][0]['new_values']['updated_at'])
    )
    assert metrics[0].process_cycle_efficiency == 1


def test_get_metrics_with_story_blocker(mocker):
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
        mocker,
        stories=[story], story_blockers=[blocker]
    )

    p = Pivotal()
    metrics = p.get_metrics()

    assert len(metrics) == 1
    assert metrics[0].cycle_time == get_datetime(story_accepted) - get_datetime(story_started)
    assert metrics[0].process_cycle_efficiency == (
        (get_datetime(blocked_updated) - get_datetime(blocked_start)) / metrics[0].cycle_time
    )
    assert metrics[0].num_incomplete == 0


def test_get_metrics_with_story_blocker_unresolved(mocker):
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
        mocker, 
        stories=stories, story_blockers=[blocker]
    )

    p = Pivotal()
    metrics = p.get_metrics()

    assert len(metrics) == 1
    assert metrics[0].cycle_time == get_datetime(story_accepted) - get_datetime(story_started)
    assert metrics[0].process_cycle_efficiency == 1
    assert metrics[0].num_incomplete == 1
