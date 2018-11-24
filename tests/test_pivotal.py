from datetime import datetime
import pytest

from app.metrics.pivotal import Pivotal


@pytest.fixture()
def mock_env_vars(mocker):
    mocker.patch("os.environ", {
        'TM_PIVOTAL_PAT': 'test_pat',
        'TM_PIVOTAL_PROJECT_ID': 'test_project_id'
    })


def mock_pivotal_client(mocker, created_at='2018-11-01T12:00:00Z', blocked=True):
    class MockPivotalClient:
        def __init__(self, _, project_id=None):
            pass

        def get_story_blockers(self, story_id):
            if blocked:
                return [{
                    'resolved': True,
                    'updated_at': '2018-11-05T12:00:00Z',
                    'created_at': created_at,
                }]
            else:
                return []

    mocker.patch(
        "app.metrics.pivotal.PivotalClient",
        MockPivotalClient
    )


def test_get_cycle_time(mock_env_vars):
    p = Pivotal()

    cycle_time = p.cycle_time({'accepted_at': '2018-11-11T12:00:00Z', 'created_at': '2018-11-01T12:00:00Z'})

    assert str(cycle_time) == '10 days, 0:00:00'


def test_get_cycle_time_ignores_incomplete_stories(mock_env_vars):
    p = Pivotal()

    cycle_time = p.cycle_time(
        {'created_at': '2018-11-21T12:00:00Z'}
    )

    assert cycle_time is None


def test_get_process_cycle_efficiency(mocker, mock_env_vars):
    mock_pivotal_client(mocker)

    p = Pivotal()

    process_cycle_efficiency = p.process_cycle_efficiency(
        {
            'id': '1',
            'current_state': 'accepted', 
            'created_at': '2018-11-01T10:00:00Z',
            'accepted_at': '2018-11-06T12:00:00Z'
        }
    )
    assert process_cycle_efficiency == 0.21311475409836064


def test_get_process_cycle_efficiency_no_blockers(mocker, mock_env_vars):
    mock_pivotal_client(mocker, blocked=False)

    p = Pivotal()

    process_cycle_efficiency = p.process_cycle_efficiency(
        {
            'id': '1',
            'current_state': 'accepted', 
            'created_at': '2018-11-01T10:00:00Z',
            'accepted_at': '2018-11-06T12:00:00Z'
        }
    )
    assert process_cycle_efficiency == 1
