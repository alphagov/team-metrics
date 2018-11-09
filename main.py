from jira import JIRA
from jira.exceptions import JIRAError
from jira.resources import GreenHopperResource
import os
import re


def cycle_time(issue):
    pass


def process_cycle_efficiency(issue):
    pass


def number_of_stories(sprint):
    pass


def main():
    jira = JIRA(
        basic_auth=(os.environ['TM_USER'], os.environ['TM_PAT']),
        server='https://{}.atlassian.net'.format(os.environ['TM_HOST']),
        options={'agile_rest_path': GreenHopperResource.AGILE_BASE_REST_PATH}
    )

    # # Get all projects viewable by anonymous users.
    projects = jira.projects()

    for project in projects:
        # issues_in_project = jira.search_issues(
        #     'project={} AND SPRINT not in (closedSprints() AND sprint not in futureSprints())'.format(project.key)
        # )

        # issues_in_sprint = jira.search_issues(
        #     'project={} AND SPRINT in (2)'.format(project.key)
        # )
        # for value in issues_in_sprint:
        #     print(value)

        boards = jira.boards(projectKeyOrID=project.id)
        for board in boards:
            print("board:", board)
            try:
                # print("sprints", jira.sprints(board.id))
                for sprint in jira.sprints(board.id):
                    if sprint.raw['state'] == 'future':
                        continue
                    print("sprint: {}, {}, {} - {}".format(sprint.id, sprint.name, sprint.raw['startDate'], sprint.raw['endDate']))
                    print("sprint whole: {}".format(sprint.raw))

            except JIRAError as e:
                print(e)



if __name__ == "__main__":
    main()
