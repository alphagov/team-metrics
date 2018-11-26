import os


class Metrics:
    def __init__(self, started_on, ended_on, source, cycle_time, process_cycle_efficiency, num_stories, num_incomplete):
        self.started_on = started_on
        self.ended_on = ended_on
        self.source = source
        self.cycle_time = cycle_time
        self.process_cycle_efficiency = process_cycle_efficiency
        self.num_stories = num_stories
        self.num_incomplete = num_incomplete

    def strfdelta(self, tdelta, fmt):
        d = {"days": tdelta.days}
        d["hours"], rem = divmod(tdelta.seconds, 3600)
        d["minutes"], d["seconds"] = divmod(rem, 60)
        return fmt.format(**d)

    def get_csv_line(self):
        return "{}, {},{},{},{},{},{}\n".format(
            self.started_on,
            self.ended_on,
            self.source,
            self.strfdelta(self.cycle_time, "{days} days {hours:02d}:{minutes:02d}:{seconds:02d}") if self.cycle_time else "0",
            self.process_cycle_efficiency,
            self.num_stories,
            self.num_incomplete
        )


def create_csv_header():
    with open(os.environ['TM_CSV_FILENAME'], 'w') as csv:
        csv.writelines(
            'Started on, Ended on, Source, Cycle time, Process cycle efficiency, Number of stories, Incomplete stories\n')


def write_csv_line(metrics):
    with open(os.environ['TM_CSV_FILENAME'], 'a') as csv:
        csv.writelines(metrics.get_csv_line())