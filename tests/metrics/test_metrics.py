from datetime import datetime, timedelta
import pytest

from app.metrics import Metrics, dump_json
from app.source import (
    get_datetime,
    get_process_cycle_efficiency,
    get_quarter_daterange,
    get_time_diff
)


@pytest.mark.parametrize('quarter,expected_datetime_start,expected_datetime_end', [
    (3, datetime(2018, 10, 8, 0, 0), datetime(2019, 1, 4, 0, 0)),
    (4, datetime(2019, 1, 14, 0, 0), datetime(2019, 4, 12, 0, 0))
])
def test_get_quarter_daterange(quarter, expected_datetime_start, expected_datetime_end):
    q_start, q_end = get_quarter_daterange(2018, quarter)
    assert q_start == expected_datetime_start
    assert q_end == expected_datetime_end


def test_only_get_cycle_time():
    created_at = '2018-11-01T12:00:00Z'
    accepted_at = '2018-11-11T12:00:00Z'
    cycle_time = get_time_diff(created_at, accepted_at)

    # only 6 days as 3,4,10,11 of November 2018 are Sat / Sun
    assert str(cycle_time) == '6 days, 0:00:00'


def test_get_cycle_time_ignores_incomplete_stories():
    created_at = '2018-11-01T12:00:00Z'
    cycle_time = get_time_diff(created_at)

    assert cycle_time is None


def test_get_process_cycle_efficiency():
    process_cycle_efficiency = get_process_cycle_efficiency(
        timedelta(days=2), blocked_time=timedelta(days=1)
    )
    assert process_cycle_efficiency == 0.5


def test_get_process_cycle_efficiency_no_blockers():
    process_cycle_efficiency = get_process_cycle_efficiency(timedelta(days=2))
    assert process_cycle_efficiency == 1


def test_dump_json():
    m = Metrics(
        '1',
        'test_sprint',
        '2018-11-01T12:00',
        '2018-11-08T12:00',
        'jira',
        timedelta(days=1),
        '1',
        1,
        0

    )

    from unittest.mock import patch, mock_open
    with patch("builtins.open", mock_open()) as mock_file:
        dump_json('test', [m])
        mock_file.assert_called_with("data/test.json", 'w')
        mock_file().write.assert_called_once_with(
            '[{"project_id": "1", "sprint_id": "test_sprint", "started_on": "2018-11-01T12:00", ' +
            '"ended_on": "2018-11-08T12:00", "source": "jira", "avg_cycle_time": "1 days 00:00:00", '
            '"process_cycle_efficiency": "1", "num_completed": 1, "num_incomplete": 0}]')
