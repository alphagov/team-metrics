from datetime import datetime, timedelta
import pytest

from team_metrics.source import get_datetime, get_cycle_time, get_process_cycle_efficiency


def mock_pivotal_client(created_at='2018-11-01T12:00:00Z', resolved=True):
    class MockPivotalClient:
        def __init__(self, project_id=None):
            pass
    return MockPivotalClient()


def test_get_cycle_time():
    created_at = '2018-11-01T12:00:00Z'
    accepted_at = '2018-11-11T12:00:00Z'
    cycle_time = get_cycle_time(created_at, accepted_at=accepted_at)

    assert str(cycle_time) == '10 days, 0:00:00'


def test_get_cycle_time_ignores_incomplete_stories():
    created_at = '2018-11-01T12:00:00Z'
    cycle_time = get_cycle_time(created_at)

    assert cycle_time is None


def test_get_process_cycle_efficiency():
    process_cycle_efficiency = get_process_cycle_efficiency(
        timedelta(days=2), blocked_time=timedelta(days=1)
    )
    assert process_cycle_efficiency == 0.5


def test_get_process_cycle_efficiency_no_blockers():
    process_cycle_efficiency = get_process_cycle_efficiency(timedelta(days=2))
    assert process_cycle_efficiency == 1
