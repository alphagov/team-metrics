from datetime import datetime, timedelta
import re
import yaml

DATETIME_PATTERN = r'(^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}).*'
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


def get_quarter_daterange(year, quarter):
    # Q1 starts in April, start of tax year
    num_firebreak = quarter - 1
    start_week_num = quarter * 13 + num_firebreak

    if start_week_num > 52:
        start_week_num -= 53
        year += 1

    start_week = "{}-W{}".format(year, start_week_num)
    start_date = datetime.strptime(start_week + '-1', "%Y-W%W-%w")

    end_week_num = start_week_num + 12
    if end_week_num > 52:
        end_week_num -= 53
        year += 1

    end_week = "{}-W{}".format(year, end_week_num)

    end_date = datetime.strptime(end_week + '-5', "%Y-W%W-%w")

    return start_date, end_date


def get_datetime(datetime_str):
    matched_datetime = re.search(DATETIME_PATTERN, datetime_str)
    if matched_datetime:
        return datetime.strptime(matched_datetime.group(1), DATETIME_FORMAT)


def get_time_diff(started_at, ended_at=None):
    def count_days_on_weekends(start, end):
        weekend_count = 0
        while start <= end:
            if start.weekday() in {5, 6}:
                weekend_count += 1
            start += timedelta(days=1)
        return weekend_count

    if ended_at:
        # if start or end is on a weekend should the day be pushed to Friday / Monday?
        # As otherwise that day will be lost as it lands on the weekend
        start = get_datetime(started_at) if type(started_at) is str else started_at
        end = get_datetime(ended_at) if type(ended_at) is str else ended_at
        weekend_days = count_days_on_weekends(start, end)
        return end - start - timedelta(days=weekend_days)


def get_process_cycle_efficiency(cycle_time, blocked_time=None):
    if blocked_time:
        return (cycle_time - blocked_time) / cycle_time

    return 1  # no blocked time so 100% efficient


class Base:
    def get_metrics(self, last_num_weeks=None):
        pass
