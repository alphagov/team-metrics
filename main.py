#!/usr/bin/env python
import os
import sys

from app import create_csv_header, write_csv_line, dump_json, db
from app.daos.dao_team_metric import dao_add_sprint
from app.source.jira import Jira
from app.source.pivotal import Pivotal
from app.source.trello import Trello
from app.source.github import Github


def get_metrics_tool(choice):
    if choice in ['j', 'a']:
        return Jira(os.environ['TM_JIRA_PROJECT']), os.environ['TM_JIRA_PROJECT']
    if choice in ['p', 'a']:
        return Pivotal(os.environ['TM_PIVOTAL_PROJECT_ID']), os.environ['TM_PIVOTAL_PROJECT_ID']
    if choice in ['t', 'a']:
        return Trello(), None
    if choice in ['g', 'a']:
        return Github(), None


def main():
    def get_metrics(choice):
        m, key = get_metrics_tool(choice)

        create_csv_header(key)

        metrics = m.get_metrics(last_num_weeks=12)
        db.init()

        for metric in metrics:
            write_csv_line(key, metric)
            dao_add_sprint(metric)

        dump_json(key, metrics)

    if len(sys.argv) > 1:
        get_metrics(sys.argv[1])
    else:
        while True:
            choice = input("\nCollect team metrics from (j)ira, (p)ivotal, (t)rello, (g)ithub, (a)ll, e(x)it:")

            if choice == 'x':
                exit(0)
            else:
                get_metrics(choice)


if __name__ == "__main__":
    main()
