from datetime import datetime, timedelta
import pytest

from app.metrics import Metrics, dump_json
from app.source import (
    get_bi_weekly_sprint_dates,
    get_date_string,
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


@pytest.mark.parametrize('_datetime,expected_date', [
    ('2019-01-01 12:00:00', '2019-01-01'),
    ('2018-09-25 23:00:00', '2018-09-26'),
])
def test_get_date_string(_datetime, expected_date):
    assert get_date_string(_datetime) == expected_date


def test_get_bi_weekly_sprints():
    q_start, q_end = get_quarter_daterange(2018, 3)
    sprints = get_bi_weekly_sprint_dates(q_start, q_end)

    assert len(sprints) == 7
    assert sprints[0]['started_on'] == '2018-10-08 00:00:00'
    assert sprints[0]['ended_on'] == '2018-10-21 23:59:59'
    assert sprints[-1]['started_on'] == '2018-12-31 00:00:00'
    assert sprints[-1]['ended_on'] == '2019-01-03 23:59:59'


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
            '''[{"project_id": "1", "sprint_id": "test_sprint", "started_on": "2018-11-01T12:00", '''
            '''"ended_on": "2018-11-08T12:00", "source": "jira", "avg_cycle_time": "1 days 00:00:00", '''
            '''"process_cycle_efficiency": "1", "num_completed": 1, "num_incomplete": 0}]''')
