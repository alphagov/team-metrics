import json
from datetime import timedelta


class Metrics:
    def __init__(
            self,
            project_id,
            sprint_id,
            started_on,
            ended_on,
            source,
            avg_cycle_time,
            process_cycle_efficiency,
            num_completed,
            num_incomplete
    ):
        self.project_id = project_id
        self.sprint_id = str(sprint_id)
        self.started_on = started_on
        self.ended_on = ended_on
        self.source = source
        self.avg_cycle_time = int(avg_cycle_time.total_seconds()) if avg_cycle_time else 0
        self.process_cycle_efficiency = process_cycle_efficiency
        self.num_completed = num_completed
        self.num_incomplete = num_incomplete

    def __repr__(self):
        return str({
            'project_id': self.project_id,
            'sprint_id': self.sprint_id,
            'started_on': self.started_on,
            'ended_on': self.ended_on,
            'source': self.source,
            'avg_cycle_time': self.avg_cycle_time,
            'process_cycle_efficiency': self.process_cycle_efficiency,
            'num_completed': self.num_completed,
            'num_incomplete': self.num_incomplete
        })

    def get_csv_line(self):
        return "{} ,{} ,{} ,{} ,{} ,{} ,{} ,{} ,{}\n".format(
            self.project_id,
            self.sprint_id,
            self.started_on,
            self.ended_on,
            self.source,
            get_cycletime_from_seconds(
                self.avg_cycle_time
            ) if self.avg_cycle_time else "0",
            self.process_cycle_efficiency,
            self.num_completed,
            self.num_incomplete
        )


def get_cycletime_from_seconds(cycle_time_seconds):
    fmt = "{days} days {hours:02d}:{minutes:02d}:{seconds:02d}"
    tdelta = timedelta(seconds=cycle_time_seconds)
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


def create_csv_header(filename):
    with open('data/{}.csv'.format(filename), 'w') as csv:
        csv.writelines(
            "Project id, Started on, Ended on, Source, Cycle time, " +
            "Process cycle efficiency, Number of stories, Incomplete stories\n"
        )


def write_csv_line(filename, metrics):
    print('write CSV: {} - {}'.format(metrics.project_id, metrics.sprint_id))
    with open('data/{}.csv'.format(filename), 'a') as csv:
        csv.writelines(metrics.get_csv_line())


def dump_json(filename, metrics):
    def to_dict(obj):
        obj_dict = obj.__dict__
        obj_dict['avg_cycle_time'] = get_cycletime_from_seconds(obj_dict['avg_cycle_time'])
        return obj_dict

    with open('data/{}.json'.format(filename), 'w') as jsonfile:
        jsonfile.write(json.dumps(metrics, default=to_dict))
