from datetime import datetime, timedelta
import os
from math import ceil

from app.metrics import Metrics
from app.source import (
    Base,
    get_date_string,
    get_datetime,
    get_process_cycle_efficiency,
    get_quarter_daterange,
    get_time_diff
)

from app.pivotal_client import ApiError, PivotalClient


class Pivotal(Base):
    def __init__(self, project_id=None):
        self.pivotal = PivotalClient(os.environ['TM_PIVOTAL_PAT'], project_id=project_id)

    def get_blocked_time(self, story_id):
        blocked_time = None
        for blocker in [b for b in self.pivotal.get_story_blockers(story_id) if b.get('resolved')]:
            updated_at = blocker['updated_at']
            created_at = blocker['created_at']
            # blocked_time = get_datetime(updated_at) - get_datetime(created_at)
            blocked_time = get_time_diff(created_at, updated_at)
        return blocked_time

    def get_started_at(self, story_id):
        activities = self.pivotal.get_story_activities(story_id)
        for activity in activities:
            if activity['highlight'] == 'started':
                for story in [a for a in activity['changes'] if a['kind'] == 'story']:
                    return story['new_values']['updated_at']
        print(">>>> Not started", story_id)

    def get_iteration_range(self, year, quarter):
        q_start, _ = get_quarter_daterange(year, quarter)

        project_info = self.pivotal.get_project()

        date_diff = q_start - get_datetime(project_info['start_time'])

        s = date_diff.total_seconds()
        weeks, _ = divmod(s, 7 * 24 * 60 * 60)

        iteration_length = project_info['iteration_length']
        current_iteration = project_info['current_iteration_number']

        iteration_start = int(weeks / iteration_length)
        iteration_end = int(iteration_start + 12 / iteration_length)
        if iteration_end > current_iteration:
            iteration_end = current_iteration
        num_iterations = iteration_end - iteration_start

        return iteration_start, num_iterations

    def get_metrics(self, year=None, quarter=None):
        print("Pivotal")

        iteration_start = num_iterations = 0

        if year and quarter:
            iteration_start, num_iterations = self.get_iteration_range(year, quarter)

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

                    _cycle_time = get_time_diff(
                        started_at, story['accepted_at']
                    )

                    if not _cycle_time:
                        continue

                    if cycle_time:
                        cycle_time += _cycle_time
                    else:
                        cycle_time = _cycle_time

                    print('  cycle_time: {}'.format(_cycle_time))

                    if story.get('accepted_at'):
                        _process_cycle_efficiency = get_process_cycle_efficiency(
                            _cycle_time, self.get_blocked_time(story['id']))
                        if _process_cycle_efficiency < 0:
                            # this happens when a story gets started, has blockers,
                            #   so gets unstarted in a previous iteration
                            #   then restarted in this iteration and accepted
                            # we need to decide whether we include the cycle time of a previous iteration?
                            # also should teams unstart and then restart stories in a different iteration
                            continue

                        print("  process_cycle_efficiency: {}".format(_process_cycle_efficiency))

                        if process_cycle_efficiency:
                            process_cycle_efficiency += _process_cycle_efficiency
                        else:
                            process_cycle_efficiency = _process_cycle_efficiency
            except ApiError as e:
                print('api error', e)

            num_stories_complete = len([s for s in iteration['stories'] if s['current_state'] == 'accepted'])
            num_stories_incomplete = len(iteration['stories']) - num_stories_complete
            print("\n  Number of accepted stories: {}".format(num_stories_complete))
            print("\n  Number of incomplete stories: {}".format(num_stories_incomplete))

            m = Metrics(
                self.pivotal.project_id,
                iteration["number"],
                get_date_string(iteration["start"]),
                get_date_string(iteration["finish"]),
                "pivotal",
                0 if not cycle_time else cycle_time / num_stories_complete,
                (process_cycle_efficiency / num_stories_complete) if num_stories_complete else 0,
                num_stories_complete,
                num_stories_incomplete
            )
            metrics.append(m)
        return metrics
