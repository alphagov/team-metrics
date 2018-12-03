#!/usr/bin/env python
import sys

from app import create_csv_header
from app.metrics.jira import Jira
from app.metrics.pivotal import Pivotal
from app.metrics.trello import Trello
from app.metrics.github import Github


def get_metrics_tool(choice):
    if choice in ['j', 'a']:
        return Jira('CYB')
    if choice in ['p', 'a']:
        return Pivotal()
    if choice in ['t', 'a']:
        return Trello()
    if choice in ['g', 'a']:
        return Github()


def main():
    def get_metrics(choice):
        m = get_metrics_tool(choice)
        for metric in m.get_metrics(last_num_weeks=12):
            print(metric)

    create_csv_header()

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
