#!/usr/bin/env python
import os
import sys

from app import db
from app.metrics import create_csv_header, write_csv_line, dump_json
from app.daos.dao_team_metric import dao_upsert_sprint
from app.source.jira import Jira
from app.source.pivotal import Pivotal
from app.source.trello import Trello
from app.source.github import Github


def get_metrics_tool(choice, sprint_id=None):
    if choice in ['j', 'a']:
        return Jira(os.environ['TM_JIRA_PROJECT'], sprint_id=sprint_id), os.environ['TM_JIRA_PROJECT']
    if choice in ['p', 'a']:
        return Pivotal(os.environ['TM_PIVOTAL_PROJECT_ID']), os.environ['TM_PIVOTAL_PROJECT_ID']
    if choice in ['t', 'a']:
        return Trello(os.environ['TM_TRELLO_BOARD_ID'], sprint_id=sprint_id), os.environ['TM_TRELLO_BOARD_ID']
    if choice in ['g', 'a']:
        return Github(os.getenv("TM_TEAM_ID")), None


def main():
    def get_metrics(choice, sprint_id=None):
        m, key = get_metrics_tool(choice, sprint_id=sprint_id)

        create_csv_header(key)

        db.init()

        metrics = m.get_metrics(year=2018, quarter=3)

        if choice != 'g':
            for metric in metrics:
                write_csv_line(key, metric)
                dao_upsert_sprint(metric)

            dump_json(key, metrics)

    if len(sys.argv) > 1:
        if sys.argv[1] == "gt":
            github = Github()
            github.get_teams()
        else:
            get_metrics(sys.argv[1], None if len(sys.argv) <= 2 else sys.argv[2])
    else:
        while True:
            choice = input("\nCollect team metrics from (j)ira, (p)ivotal, (t)rello, (g)ithub, (a)ll, e(x)it:")

            if choice == 'x':
                exit(0)
            else:
                get_metrics(choice)


if __name__ == "__main__":
    main()
