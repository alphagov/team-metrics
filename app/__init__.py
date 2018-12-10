import json
import os
import uuid
from datetime import timedelta

from flask import Flask

from app.metrics_db import Metrics_DB

db = Metrics_DB()
application = Flask('app')


def create_app():
    db.init()

    register_blueprint(application)

    return application


def register_blueprint(application):
    from app.routes.index import index_blueprint
    from app.routes.cyber_team import cyber_team_blueprint
    from app.routes.paas_team import paas_team_blueprint
    from app.routes.re_programme import re_programme_blueprint
    from app.routes.techops_team import techop_team_blueprint
    from app.routes.assets import assets_blueprint

    application.register_blueprint(index_blueprint)
    application.register_blueprint(cyber_team_blueprint)
    application.register_blueprint(paas_team_blueprint)
    application.register_blueprint(re_programme_blueprint)
    application.register_blueprint(techop_team_blueprint)
    application.register_blueprint(assets_blueprint)


class Metrics:
    def __init__(
            self,
            project_id,
            sprint_id,
            started_on,
            ended_on,
            source,
            cycle_time,
            process_cycle_efficiency,
            num_completed,
            num_incomplete
    ):
        self.project_id = project_id
        self.sprint_id = sprint_id
        self.started_on = started_on
        self.ended_on = ended_on
        self.source = source
        self.cycle_time = cycle_time
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
            'cycle_time': self.cycle_time,
            'process_cycle_efficiency': self.process_cycle_efficiency,
            'num_completed': self.num_completed,
            'num_incomplete': self.num_incomplete
        })

    def strfdelta(self, tdelta, fmt):
        d = {"days": tdelta.days}
        d["hours"], rem = divmod(tdelta.seconds, 3600)
        d["minutes"], d["seconds"] = divmod(rem, 60)
        return fmt.format(**d)

    def get_csv_line(self):
        return "{} ,{} ,{} ,{} ,{} ,{} ,{} ,{} ,{}\n".format(
            self.project_id,
            self.sprint_id,
            self.started_on,
            self.ended_on,
            self.source,
            self.strfdelta(
                self.cycle_time,
                "{days} days {hours:02d}:{minutes:02d}:{seconds:02d}"
            ) if self.cycle_time else "0",
            self.process_cycle_efficiency,
            self.num_completed,
            self.num_incomplete
        )


def create_csv_header(filename):
    with open('data/{}.csv'.format(filename), 'w') as csv:
        csv.writelines(
            "Project id, Started on, Ended on, Source, Cycle time, " +
            "Process cycle efficiency, Number of stories, Incomplete stories\n"
        )


def write_csv_line(filename, metrics):
    with open('data/{}.csv'.format(filename), 'a') as csv:
        csv.writelines(metrics.get_csv_line())


def dump_json(filename, metrics):
    def to_dict(obj):
        if type(obj) == timedelta:
            hours, remainder = divmod(obj.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return "{} days {}:{}:{}".format(obj.days, hours, minutes, seconds)
        else:
            return obj.__dict__

    with open('data/{}.json'.format(filename), 'w') as jsonfile:
        jsonfile.write(json.dumps(metrics, default=to_dict))
