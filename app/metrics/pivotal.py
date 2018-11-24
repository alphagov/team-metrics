from datetime import datetime, timedelta
import os

from app import Metrics, write_csv_line
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

        return _cycle_time
        # return self.strfdelta(_cycle_time, "{days} days {hours:02d}:{minutes:02d}:{seconds:02d}")

    def process_cycle_efficiency(self, story):
        print("  process cycle efficiency")
        print("    {}".format(story['current_state']))
        blocked_time = 0
        for blocker in [b for b in self.pivotal.get_story_blockers(story['id']) if b['resolved']]:
        # for blocker in self.pivotal.get_story_blockers(story['id']):
            # updated_at = datetime.strptime(blocker['updated_at'], self.DATETIME_FORMAT) if blocker['resolved'] else datetime.now()
            updated_at = datetime.strptime(blocker['updated_at'], self.DATETIME_FORMAT)
            created_at = datetime.strptime(blocker['created_at'], self.DATETIME_FORMAT)
            blocked_time = updated_at - created_at

        if story.get('accepted_at'):
            # print("    created: {} - blocked: {} - accepted: {}".format(story['created_at'], blocked_time, story['accepted_at']))
            _cycle_time = self.cycle_time(story)
            if blocked_time:
                return (_cycle_time - blocked_time) / _cycle_time
            return 1

    def get_metrics(self):
        print("Pivotal")
        for iteration in self.pivotal.get_project_iterations():
            _cycle_time = _process_cycle_efficiency = None
            _num_stories_complete = _num_stories_incomplete = 0
            try:
                print("\nIteration: {} - {}".format(iteration['start'], iteration['finish']))
                for story in iteration['stories']:
                    print(story['name'])
                    if _cycle_time:
                        _cycle_time += self.cycle_time(story)
                    else:
                        _cycle_time = self.cycle_time(story)
                    print('    cycle_time: {}'.format(_cycle_time))
                    pce = self.process_cycle_efficiency(story)

                    if pce:
                        print("    process_cycle_efficiency: {}".format(pce))
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
                "{} - {}".format(iteration["start"], iteration["finish"]),
                "pivotal",
                _cycle_time,
                _process_cycle_efficiency / _num_stories_complete,
                _num_stories_complete
            )
            write_csv_line(m)
