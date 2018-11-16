#!/usr/bin/env python
from app.jira import Jira
from app.pivotal import Pivotal


def main():
    while True:
        choice = input("\nCollect team metrics from (j)ira, (p)ivotal, (a)ll, e(x)it:")

        if choice in ['j', 'a']:
            jira = Jira()
            jira.get_metrics()
        if choice in ['p', 'a']:
            pivotal = Pivotal()
            pivotal.get_metrics()
        if choice == 'x':
            break


if __name__ == "__main__":
    main()
