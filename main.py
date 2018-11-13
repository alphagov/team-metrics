#!/usr/bin/env python
from datetime import timedelta
import os
import re

from jira import JIRA
from jira.exceptions import JIRAError
from jira.resources import GreenHopperResource

from pivotalclient import PivotalClient

class Jira(object):
    sprint_info_field_name = ''

    def __init__(self):
        self.jira = JIRA(
            basic_auth=(os.environ['TM_USER'], os.environ['TM_JIRA_PAT']),
            server='https://{}.atlassian.net'.format(os.environ['TM_JIRA_HOST']),
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

    def get_pivotal_metrics(self):
        print("Pivotal")
        for iteration in self.pivotal.get_project_iterations():
            print("\nIteration: {} - {}".format(iteration['start'], iteration['finish']))
            for story in iteration['stories']:
                print(story['name'])
                self.cycle_time(story)
                self.process_cycle_efficiency(story)

            self.cycle_time_details(self.pivotal.get_project_cycle_time_details(iteration['number']))

            print("\n  Number of accepted stories: {}".format(len([s for s in iteration['stories'] if s['current_state'] == 'accepted'])))


def main():
    while True:
        choice = input("\nCollect team metrics from (j)ira, (p)ivotal, (a)ll, e(x)it:")

        if choice in ['j', 'a']:
            jira = Jira()
            jira.get_jira_metrics()
        if choice in ['p', 'a']:
            pivotal = Pivotal()
            pivotal.get_pivotal_metrics()
        if choice == 'x':
            break


if __name__ == "__main__":
    main()
