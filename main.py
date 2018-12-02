#!/usr/bin/env python
import sys

from app import create_csv_header
from app.metrics.jira import Jira
from app.metrics.pivotal import Pivotal
from app.metrics.trello import Trello
from app.metrics.github import Github


def get_metrics_from_tool(choice):
    if choice in ['j', 'a']:
        return Jira('CYB')
        # jira.get_metrics()
    if choice in ['p', 'a']:
        return Pivotal()
        # pivotal.get_metrics(last_num_weeks=12)
    if choice in ['t', 'a']:
        return Trello()
        # trello.get_metrics()
    if choice in ['g', 'a']:
        return Github()
        # github.get_metrics()


def main():
    create_csv_header()
    if len(sys.argv) > 1:
        m = get_metrics_from_tool(sys.argv[1])
        m.get_metrics(last_num_weeks=12)
    else:
        while True:
            choice = input("\nCollect team metrics from (j)ira, (p)ivotal, (t)rello, (g)ithub, (a)ll, e(x)it:")

            if choice == 'x':
                exit(0)
            else:
                m = get_metrics_from_tool(choice)
                m.get_metrics(last_num_weeks=12)


if __name__ == "__main__":
    main()
