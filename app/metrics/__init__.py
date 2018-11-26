from datetime import datetime


DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def get_datetime(_datetime):
    return datetime.strptime(_datetime, DATETIME_FORMAT)


def get_cycle_time(created_at, accepted_at=None):
    _cycle_time = None
    if accepted_at:
        _cycle_time = get_datetime(accepted_at) - get_datetime(created_at)

    return _cycle_time


def get_process_cycle_efficiency(cycle_time, blocked_time=None):
    if blocked_time:
        return (cycle_time - blocked_time) / cycle_time

    return 1  # no blocked time so 100% efficient
