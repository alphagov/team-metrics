import os
import re
from datetime import datetime, timedelta

from jira import JIRA
from jira.exceptions import JIRAError
from jira.resources import GreenHopperResource

from team_metrics import Metrics
from team_metrics.source import Base, get_datetime, get_cycle_time, get_process_cycle_efficiency


class Jira(Base):
    sprint_info_field_name = ''

    def __init__(self, project_id=None):
        self.jira = JIRA(
            basic_auth=(os.environ['TM_JIRA_USER'], os.environ['TM_JIRA_PAT']),
            server='https://{}.atlassian.net'.format(os.environ['TM_JIRA_HOST']),
            options={'agile_rest_path': GreenHopperResource.AGILE_BASE_REST_PATH}
        )
        self.project_id = project_id

    def get_cycle_time(self, issue):
        issue = self.jira.issue(issue.id, expand='changelog')
        changelog = issue.changelog
        started_at_list = []
        done_at = None
        for history in changelog.histories:
            for item in history.items:
                if item.field == 'status':
                    if item.toString == 'In Progress':
                        started_at_list.append(history.created)
                    if item.toString == 'Done':
                        done_at = history.created

        if started_at_list and done_at:
            started_at_list.sort()
            return get_cycle_time(started_at_list[0], done_at)

    def get_blocked_time(self, issue):
        issue = self.jira.issue(issue.id, expand='changelog')
        changelog = issue.changelog
        blocked_start = []
        blocked_end = []
        for history in changelog.histories:
            for item in history.items:
                if item.field == 'status':
                    if item.toString == 'Blocked':
                        blocked_start.append(history.created)
                    if item.fromString == "Blocked":
                        blocked_end.append(history.created)

        if blocked_start and blocked_end:
            blocked_time = None
            for i, start in enumerate(blocked_start):
                end = blocked_end[i]
                if blocked_time:
                    blocked_time += get_datetime(end) - get_datetime(start)
                else:
                    blocked_time = get_datetime(end) - get_datetime(start)

            return blocked_time

    def get_metrics(self, last_num_weeks=None):
        metrics = []
        projects = self.jira.projects()
        for project in projects:
            if self.project_id and project.key != self.project_id:
                continue

            boards = self.jira.boards(projectKeyOrID=project.id)
            for board in boards:
                print("board:", board)
                try:
                    for sprint in self.jira.sprints(board.id):
                        if sprint.raw['state'] == 'future':
                            continue

                        # sprints before
                        if (last_num_weeks and (
                                sprint.raw['startDate'] <
                                str(datetime.today() - timedelta(weeks=last_num_weeks) - timedelta(weeks=2)) or 
                                sprint.raw['startDate'] > str(datetime.today() - timedelta(weeks=2)))
                        ):
                            continue

                        stories_completed = 0
                        cycle_time = process_cycle_efficiency = None

                        print("\nsprint: {}, {}, {} - {}".format(
                            sprint.id, sprint.name, sprint.raw['startDate'], sprint.raw['endDate'])
                        )
                        sprint_issues = self.jira.search_issues(
                            'project={} AND SPRINT in ({})'.format(project.id, sprint.id)
                        )
                        for issue in sprint_issues:
                            _cycle_time = self.get_cycle_time(issue)
                            if not _cycle_time:
                                continue

                            if cycle_time:
                                cycle_time += _cycle_time
                            else:
                                cycle_time = _cycle_time

                            stories_completed += 1

                            print("  cycle time: {}".format(_cycle_time))

                            print("blocked time: {}".format(self.get_blocked_time(issue)))

                            _process_cycle_efficiency = get_process_cycle_efficiency(
                                    _cycle_time, self.get_blocked_time(issue))
                            if process_cycle_efficiency:
                                process_cycle_efficiency += _process_cycle_efficiency
                            else:
                                process_cycle_efficiency = _process_cycle_efficiency

                            print("  process cycle efficiency: {}".format(_process_cycle_efficiency))

                        stories_incomplete = len(sprint_issues) - stories_completed
                        print("  issues completed: ", str(stories_completed))
                        print("  issues incomplete: ", str(stories_incomplete))

                        m = Metrics(
                            project.key,
                            sprint.id,
                            sprint.raw['startDate'],
                            sprint.raw['endDate'],
                            "jira",
                            cycle_time / stories_completed,
                            (process_cycle_efficiency / stories_completed) if stories_completed else 0,
                            stories_completed,
                            stories_incomplete
                        )
                        metrics.append(m)

                except JIRAError as e:
                    pass
            if self.project_id:
                return metrics
        return metrics
