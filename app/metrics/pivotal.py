from datetime import datetime, timedelta
import os

from app import Metrics, write_csv_line
from app.metrics import get_cycle_time, get_datetime, get_process_cycle_efficiency
from app.pivotal_client import ApiError, PivotalClient


class Pivotal:
    DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

    def __init__(self):
        self.pivotal = PivotalClient(os.environ['TM_PIVOTAL_PAT'], project_id=os.environ['TM_PIVOTAL_PROJECT_ID'])

    def get_blocked_time(self, story_id):
        blocked_time = None
        for blocker in [b for b in self.pivotal.get_story_blockers(story_id) if b.get('resolved')]:
            updated_at = blocker['updated_at']
            created_at = blocker['created_at']
            blocked_time = get_datetime(updated_at) - get_datetime(created_at)
        return blocked_time

    def get_started_at(self, story_id):
        activities = self.pivotal.get_story_activities(story_id)
        for activity in activities:
            if activity['highlight'] == 'started':
                return activity['changes'][0]['new_values']['updated_at']

    def get_iteration_range(self, last_num_weeks):
        project_info = self.pivotal.get_project()

        iteration_length = project_info['iteration_length']
        num_iterations = project_info['number_of_done_iterations_to_show']
        current_iteration_number = project_info['current_iteration_number']

        iteration_interval = last_num_weeks % iteration_length

        iteration_end = current_iteration_number - 1
        iteration_start = iteration_end - iteration_interval - 1
        if iteration_start < 1:
            iteration_start = 1

        return iteration_start, iteration_end

    def get_metrics(self, last_num_weeks=None):
        print("Pivotal")

        iteration_start = iteration_end = 0

        if last_num_weeks:
            iteration_start, iteration_end = self.get_iteration_range(last_num_weeks)

        metrics = []
        for iteration in self.pivotal.get_project_iterations():
            if iteration_start > 0 and (iteration['number'] < iteration_start or iteration['number'] > iteration_end):
                continue

            _cycle_time = _process_cycle_efficiency = None
            _num_stories_complete = _num_stories_incomplete = 0
            try:
                print("\nIteration: {} - {}".format(iteration['start'], iteration['finish']))
                for story in iteration['stories']:                    
                    if not story.get('accepted_at'):
                        continue

                    print(story['name'])

                    started_at = self.get_started_at(story['id'])

                    if _cycle_time:
                        _cycle_time += get_cycle_time(
                            started_at, story['accepted_at']
                        )
                    else:
                        _cycle_time = get_cycle_time(
                            started_at, story['accepted_at']
                        )
                    
                    print('  cycle_time: {}'.format(_cycle_time))

                    if story.get('accepted_at'):
                        pce = get_process_cycle_efficiency(_cycle_time, self.get_blocked_time(story['id']))
                        print("  process_cycle_efficiency: {}".format(pce))

                        if _process_cycle_efficiency:
                            _process_cycle_efficiency += pce
                        else:
                            _process_cycle_efficiency = pce
            except ApiError as e:
                print('api error', e)

            _num_stories_complete = len([s for s in iteration['stories'] if s['current_state'] == 'accepted'])
            _num_stories_incomplete = len(iteration['stories']) - _num_stories_complete
            print("\n  Number of accepted stories: {}".format(_num_stories_complete))
            print("\n  Number of incomplete stories: {}".format(_num_stories_incomplete))

            m = Metrics(
                iteration["start"],
                iteration["finish"],
                "pivotal",
                _cycle_time,
                (_process_cycle_efficiency / _num_stories_complete) if _num_stories_complete else 0,
                _num_stories_complete,
                _num_stories_incomplete
            )
            metrics.append(m)
            write_csv_line(m)
        return metrics
