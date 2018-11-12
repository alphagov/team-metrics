#!/usr/bin/env python
import os
import re

from jira import JIRA
from jira.exceptions import JIRAError
from jira.resources import GreenHopperResource


class Jira(object):
    sprint_info_field_name = ''

    def __init__(self):
        self.jira = JIRA(
            basic_auth=(os.environ['TM_USER'], os.environ['TM_PAT']),
            server='https://{}.atlassian.net'.format(os.environ['TM_HOST']),
            options={'agile_rest_path': GreenHopperResource.AGILE_BASE_REST_PATH}
        )

    def cycle_time(self, fields):
        print("  cycle time")
        print("    state: {} - startDate: {} - endDate: {} - completeDate: {}".format(
            fields['state'],
            fields['startDate'],
            fields['endDate'],
            fields['completeDate'])
        )

    def process_cycle_efficiency(self, issue):
        print("  process cycle efficiency")
        issue = self.jira.issue(issue.id, expand='changelog')
        changelog = issue.changelog
        for history in changelog.histories:
            for item in history.items:
                if item.field == 'status':
                    print('    Date:' + history.created + ' From:' + item.fromString + ' To:' + item.toString)

    def get_dict_from_key_value_pair(self, input):
        kv_matches = re.search(r"\[(.+)\]", input)
        if not kv_matches:
            return None
        kv_string = kv_matches.group(1)
        try:
            kv_dict = dict(kv.split("=") for kv in kv_string.split(","))
            return dict((key, None if value == "<null>" else value) for key, value in kv_dict.items())
        except ValueError as e:
            print("###### ", e, input)
            return None

    def get_jira_metrics(self):
        # # Get all projects viewable by anonymous users.
        projects = self.jira.projects()

        for project in projects:
            sprints_found = False
            boards = self.jira.boards(projectKeyOrID=project.id)
            for board in boards:
                print("board:", board)
                try:
                    for sprint in self.jira.sprints(board.id):
                        if sprint.raw['state'] == 'future':
                            continue
                        sprints_found = True
                        stories_completed = 0

                        print("\nsprint: {}, {}, {} - {}".format(
                            sprint.id, sprint.name, sprint.raw['startDate'], sprint.raw['endDate'])
                        )
                        for issue in self.jira.search_issues(
                            'project={} AND SPRINT in ({})'.format(project.id, sprint.id)
                        ):
                            # print("*** issue whole: {}".format(issue.raw)); break

                            if not self.sprint_info_field_name:
                                for name in dir(issue.fields):
                                    sprint_info = getattr(issue.fields, name)
                                    if sprint_info and type(sprint_info) == list and \
                                        'com.atlassian.greenhopper.service.sprint.Sprint' in sprint_info[0]:
                                        self.sprint_info_field_name = name

                            if not self.sprint_info_field_name:
                                continue

                            sprint_info = getattr(issue.fields, self.sprint_info_field_name)
                            if len(sprint_info) > 1:
                                print("******** more than one sprint_info field!")
                                print(sprint_info)

                            cf = sprint_info[0]
                            fields = self.get_dict_from_key_value_pair(cf)

                            if not fields:
                                print("######## no fields available: ", cf)
                                continue

                            print("  issue: {} - {}".format(issue.id, issue.key))
                            self.cycle_time(fields)
                            self.process_cycle_efficiency(issue)

                            if fields['state'] == 'CLOSED':
                                stories_completed += 1
                        print("  stories completed: ", str(stories_completed))

                except JIRAError as e:
                    # print(e)
                    pass
            if sprints_found:
                break


def main():
    jira = Jira()
    jira.get_jira_metrics()


if __name__ == "__main__":
    main()
