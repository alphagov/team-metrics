#!/usr/bin/env python
import os
import re

from jira import JIRA
from jira.exceptions import JIRAError
from jira.resources import GreenHopperResource


def cycle_time(issue):
    pass


def process_cycle_efficiency(issue):
    pass


def get_dict_from_key_value_pair(input):
    key_value_str = re.search(r"\[(.+)\]", input).group(1)
    return dict(kv.split("=") for kv in key_value_str.split(","))


def number_of_stories_completed(jira, project, sprint):
    for issue in jira.search_issues('project={} AND SPRINT in ({})'.format(project.id, sprint.id)):
        # print("  issue whole: {}".format(issue.raw))

        # need to parse customfield_10020 for ACTIVE, startDate and endDate
        # don't always use the first entry!
        cf = issue.fields.customfield_10020[0]
        if len(issue.fields.customfield_10020) > 1:
            print("more than one customfield_10020!")
        try:
            fields = get_dict_from_key_value_pair(cf)
            print("  issue: {} - {}".format(issue.id, issue.key))
            print("    state: {} - startDate: {} - endDate: {} - completeDate: {}".format(
                fields['state'],
                fields['startDate'],
                fields['endDate'],
                fields['completeDate'])
            )

            issue = jira.issue(issue.id, expand='changelog')
            changelog = issue.changelog
            for history in changelog.histories:
                for item in history.items:
                    if item.field == 'status':
                        print('    Date:' + history.created + ' From:' + item.fromString + ' To:' + item.toString)
        except ValueError as e:
            pass


def get_jira_metrics():
    jira = JIRA(
        basic_auth=(os.environ['TM_USER'], os.environ['TM_PAT']),
        server='https://{}.atlassian.net'.format(os.environ['TM_HOST']),
        options={'agile_rest_path': GreenHopperResource.AGILE_BASE_REST_PATH}
    )

    # # Get all projects viewable by anonymous users.
    projects = jira.projects()

    for project in projects:
        boards = jira.boards(projectKeyOrID=project.id)
        for board in boards:
            print("board:", board)
            try:
                # print("sprints", jira.sprints(board.id))
                for sprint in jira.sprints(board.id):
                    if sprint.raw['state'] == 'future':
                        continue
                    print("sprint: {}, {}, {} - {}".format(sprint.id, sprint.name, sprint.raw['startDate'], sprint.raw['endDate']))
                    number_of_stories_completed(jira, project, sprint)
                    # print("sprint whole: {}".format(sprint.raw))

            except JIRAError as e:
                # print(e)
                pass


def main():
    get_jira_metrics()


if __name__ == "__main__":
    main()
