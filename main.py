#!/usr/bin/env python
import sys

from app import create_csv_header
from app.metrics.jira import Jira
from app.metrics.pivotal import Pivotal
from app.metrics.trello import Trello
from app.metrics.github import Github


def get_metrics_from_tool(choice):
    if choice in ['j', 'a']:
        jira = Jira()
        jira.get_metrics()
    if choice in ['p', 'a']:
        pivotal = Pivotal()
        pivotal.get_metrics()
    if choice in ['t', 'a']:
        trello = Trello()
        trello.get_metrics()
    if choice in ['g', 'a']:
        github = Github()
        github.get_metrics()


def main():
    create_csv_header()
    if len(sys.argv) > 1:
        get_metrics_from_tool(sys.argv[1])
    else:
        while True:
            choice = input("\nCollect team metrics from (j)ira, (p)ivotal, (t)rello, (a)ll, (g)ithub, e(x)it:")

            if choice == 'x':
                break
            else:
                get_metrics_from_tool(choice)


if __name__ == "__main__":
    main()
