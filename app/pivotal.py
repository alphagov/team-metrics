#!/usr/bin/env python
from datetime import timedelta
import os

from pivotalclient import PivotalClient
from pivotalclient import ApiError


class Pivotal:
    def __init__(self):
        self.pivotal = PivotalClient(os.environ['TM_PIVOTAL_PAT'], project_id=os.environ['TM_PIVOTAL_PROJECT_ID'])

    def cycle_time(self, story):
        print("  cycle time")
        print("    {} - {}".format(story['created_at'], story.get('accepted_at', 'N/A')))

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
                    self.cycle_time(story)
                    self.process_cycle_efficiency(story)

                if iteration.get('number'):
                    self.cycle_time_details(self.pivotal.get_project_cycle_time_details(iteration['number']))
            except ApiError as e:
                print('api error', e)

            print("\n  Number of accepted stories: {}".format(len([s for s in iteration['stories'] if s['current_state'] == 'accepted'])))
