from jira import JIRA
from jira.resources import GreenHopperResource
import os
import re


def main():
    jira = JIRA(
        basic_auth=(os.environ['TM_USER'], os.environ['TM_PAT']),
        server='https://{}.atlassian.net'.format(os.environ['TM_HOST']),
        options={'agile_rest_path': GreenHopperResource.AGILE_BASE_REST_PATH}
    )

    # # Get all projects viewable by anonymous users.
    projects = jira.projects()

    for project in projects:
        ### projectKeyOrID is not available as an argument yet as it has not been tagged in the release
        # boards = jira.boards(projectKeyOrID=project.name)
        # print("boards", boards)
        # for board in boards:

        # print("project name:", dir(project))
        # issues_in_project = jira.search_issues(
        #     'project={} AND SPRINT not in (closedSprints() AND sprint not in futureSprints())'.format(project.key)
        # )

        # for value in issues_in_project:
        #     for value in issues_in_project:
        #         print(value.key, value.fields.summary, value.fields.assignee, value.fields.reporter, value.fields.updated, value.fields.resolutiondate)
        #     # for sprint in value.fields.customfield_10004:
        #     #     sprint_name = re.findall(r"name=[^,]*", str(value.fields.customfield_10004[0]))
        #     #     print(sprint_name)

        print('sprints')
        sprints = jira.search_issues(
            'project={} AND SPRINT in (closedSprints(),openSprints())'.format(project.key)
        )

        for value in sprints:
            print(value)        

        issues_in_sprint = jira.search_issues(
            'project={} AND SPRINT in (2)'.format(project.key)
        )
        for value in issues_in_sprint:
            print(value)

        issues = jira.search_issues("project = {}".format(project))

        for issue in issues:
            print("issue:", issue)


if __name__ == "__main__":
    main()
