from datetime import datetime, timedelta
import os
from math import ceil

from team_metrics import Metrics
from team_metrics.source import Base, get_cycle_time, get_datetime, get_process_cycle_efficiency
from team_metrics.pivotal_client import ApiError, PivotalClient


class Pivotal(Base):
    def __init__(self, project_id=None):
        self.pivotal = PivotalClient(os.environ['TM_PIVOTAL_PAT'], project_id=project_id)

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
                for story in [a for a in activity['changes'] if a['kind'] == 'story']:
                    return story['new_values']['updated_at']
        print(">>>> Not started", story_id)

    def get_iteration_range(self, last_num_weeks):
        project_info = self.pivotal.get_project()

        iteration_length = project_info['iteration_length']
        current_iteration_number = project_info['current_iteration_number']

        num_iterations = int(ceil(last_num_weeks / iteration_length))

        iteration_end = current_iteration_number - 1
        iteration_start = iteration_end - num_iterations - 1

        if iteration_start < 1:
            # adjust number of iterations if attempting to get more iterations than available
            num_iterations += iteration_start
            iteration_start = 1

        return iteration_start, num_iterations

    def get_metrics(self, last_num_weeks=None):
        print("Pivotal")

        iteration_start = num_iterations = 0

        if last_num_weeks:
            iteration_start, num_iterations = self.get_iteration_range(last_num_weeks)

        print("iterations: {} to {}".format(iteration_start, iteration_start + num_iterations))

        metrics = []
        for iteration in self.pivotal.get_project_iterations(offset=iteration_start, limit=num_iterations):
            cycle_time = process_cycle_efficiency = None

            num_stories_complete = num_stories_incomplete = 0
            try:
                print("\nIteration: {} - {}".format(iteration['start'], iteration['finish']))
                for story in iteration['stories']:
                    if not story.get('accepted_at'):
                        continue

                    print(story['name'])

                    started_at = self.get_started_at(story['id'])

                    if not started_at:
                        continue

                    if cycle_time:
                        cycle_time += get_cycle_time(
                            started_at, story['accepted_at']
                        )
                    else:
                        cycle_time = get_cycle_time(
                            started_at, story['accepted_at']
                        )
                    
                    print('  cycle_time: {}'.format(cycle_time))

                    if story.get('accepted_at'):
                        pce = get_process_cycle_efficiency(cycle_time, self.get_blocked_time(story['id']))
                        print("  process_cycle_efficiency: {}".format(pce))

                        if process_cycle_efficiency:
                            process_cycle_efficiency += pce
                        else:
                            process_cycle_efficiency = pce
            except ApiError as e:
                print('api error', e)

            num_stories_complete = len([s for s in iteration['stories'] if s['current_state'] == 'accepted'])
            num_stories_incomplete = len(iteration['stories']) - num_stories_complete
            print("\n  Number of accepted stories: {}".format(num_stories_complete))
            print("\n  Number of incomplete stories: {}".format(num_stories_incomplete))

            m = Metrics(
                self.pivotal.project_id,
                iteration["start"],
                iteration["finish"],
                "pivotal",
                cycle_time,
                (process_cycle_efficiency / num_stories_complete) if num_stories_complete else 0,
                num_stories_complete,
                num_stories_incomplete
            )
            metrics.append(m)
        return metrics
