import os
import re
from datetime import datetime, timedelta

from jira import JIRA
from jira.exceptions import JIRAError
from jira.resources import GreenHopperResource

from app.metrics import Metrics
from app.source import (
    Base,
    get_date_string,
    get_datetime,
    get_process_cycle_efficiency,
    get_time_diff,
    get_quarter_daterange
)


class Jira(Base):
    sprint_info_field_name = ''

    def __init__(self, project_id=None, sprint_id=None):
        self.jira = JIRA(
            basic_auth=(os.environ['TM_JIRA_USER'], os.environ['TM_JIRA_PAT']),
            server='https://{}.atlassian.net'.format(os.environ['TM_JIRA_HOST']),
            options={'agile_rest_path': GreenHopperResource.AGILE_BASE_REST_PATH}
        )
        self.project_id = project_id
        self.sprint_id = sprint_id

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
            return get_time_diff(started_at_list[0], done_at)

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
                time_diff = get_time_diff(start, end)
                if blocked_time:
                    blocked_time += time_diff
                else:
                    blocked_time = time_diff

            return blocked_time

    def get_metrics(self, year=None, quarter=None):
        if year and quarter:
            q_start, q_end = get_quarter_daterange(year, quarter)

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

                        if self.sprint_id and str(sprint.id) != (self.sprint_id):
                            continue

                        # sprints before
                        if (
                            year and quarter and (
                                sprint.raw['startDate'] < q_start.strftime('%Y-%m-%dT%H:%M:%S') or
                                sprint.raw['startDate'] > q_end.strftime('%Y-%m-%dT%H:%M:%S')
                            )
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
                            get_date_string(sprint.raw['startDate']),
                            get_date_string(sprint.raw['endDate']),
                            "jira",
                            cycle_time / stories_completed if cycle_time else None,
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
