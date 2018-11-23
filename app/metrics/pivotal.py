from datetime import datetime, timedelta
import os

from app.pivotal_client import PivotalClient
from app.pivotal_client import ApiError


class Pivotal:
    DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

    def __init__(self):
        self.pivotal = PivotalClient(os.environ['TM_PIVOTAL_PAT'], project_id=os.environ['TM_PIVOTAL_PROJECT_ID'])

    def cycle_time(self, story):
        print("  cycle time")
        _cycle_time = None
        if story.get('accepted_at'):
            accepted_at = datetime.strptime(story['accepted_at'], self.DATETIME_FORMAT)
            created_at = datetime.strptime(story['created_at'], self.DATETIME_FORMAT)
            _cycle_time = accepted_at - created_at

        print("    {} - {} = {}".format(story['created_at'], story.get('accepted_at', 'N/A'), _cycle_time))
        return _cycle_time

    def process_cycle_efficiency(self, story):
        print("  process cycle efficiency")
        print("    {}".format(story['current_state']))
        print("    {} - {} - {}".format(story['created_at'], story['updated_at'], story.get('accepted_at')))

    def cycle_time_details(self, details):
        print("  cycle time details")
        for detail in details:
            started = timedelta(milliseconds=detail['started_time'])
            finished = timedelta(milliseconds=detail['finished_time'])
            delivered = timedelta(milliseconds=detail['delivered_time'])
            rejected = timedelta(milliseconds=detail['rejected_time'])
            total = timedelta(milliseconds=detail['total_cycle_time'])
            print("    started: {} - finished: {} - delivered: {} - total: {}, rejected: {}".format(
                started, finished, delivered, total, rejected))

    def get_metrics(self):
        print("Pivotal")
        for iteration in self.pivotal.get_project_iterations():
            try:
                print("\nIteration: {} - {}".format(iteration['start'], iteration['finish']))
                for story in iteration['stories']:
                    print(story['name'])
                    _cycle_time = self.cycle_time(story)
                    print('    cycle_time', _cycle_time)
                    self.process_cycle_efficiency(story)

                if iteration.get('number'):
                    self.cycle_time_details(self.pivotal.get_project_cycle_time_details(iteration['number']))
            except ApiError as e:
                print('api error', e)

            print("\n  Number of accepted stories: {}".format(len([s for s in iteration['stories'] if s['current_state'] == 'accepted'])))
