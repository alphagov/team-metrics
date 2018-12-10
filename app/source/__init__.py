from datetime import datetime
import re


DATETIME_PATTERN = r'(^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}).*'
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


def get_datetime(datetime_str):
    matched_datetime = re.search(DATETIME_PATTERN, datetime_str)
    if matched_datetime:
        return datetime.strptime(matched_datetime.group(1), DATETIME_FORMAT)


def get_cycle_time(started_at, accepted_at=None):
    _cycle_time = None
    if accepted_at:
        _cycle_time = get_datetime(accepted_at) - get_datetime(started_at)

    return _cycle_time


def get_process_cycle_efficiency(cycle_time, blocked_time=None):
    if blocked_time:
        return (cycle_time - blocked_time) / cycle_time

    return 1  # no blocked time so 100% efficient


class Base:
    def get_metrics(self, last_num_weeks=None):
        pass
