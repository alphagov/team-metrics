from datetime import datetime, timedelta
import re


DATETIME_PATTERN = r'(^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}).*'
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


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
        start = get_datetime(started_at)
        end = get_datetime(ended_at)
        weekend_days = count_days_on_weekends(start, end)
        return end - start - timedelta(days=weekend_days)


def get_process_cycle_efficiency(cycle_time, blocked_time=None):
    if blocked_time:
        return (cycle_time - blocked_time) / cycle_time

    return 1  # no blocked time so 100% efficient


class Base:
    def get_metrics(self, last_num_weeks=None):
        pass
