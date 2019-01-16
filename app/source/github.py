import os
from datetime import datetime, timedelta

from github3 import login
from github3.exceptions import NotFoundError

from app.metrics import Metrics
from app.source import Base, get_quarter_daterange

from app.models import GitMetric


class Github(Base):
    def __init__(self):
        self.gh = login(token=os.environ['TM_GITHUB_PAT'])

    def get_teams(self):
        for org in self.gh.organizations():
            print("Processing {} teams".format(org.url))
            for team in org.teams():
                print(team.id, team.name)

    def get_metrics(self, year=None, quarter=None):
        i = 0
        metrics = []
        q_start, q_end = get_quarter_daterange(2018, 3)
        # since = q_start.strftime('%Y-%m-%d')

        org = self.gh.organization("alphagov")
        repositories = org.team(os.getenv("TM_GITHUB_TEAM_ID")).repositories()
        for repo in repositories:
            if repo.archived == True:
                continue

            try:
                team = repo.teams().next()
                print(team)
            except NotFoundError:
                print(f"not found: {repo}")
                continue
            for team in repo.teams():
                print(repo, team)
                if team.id == os.getenv("TM_GITHUB_TEAM_ID"):
                    if team.permission != "admin":
                        break

            prs = repo.pull_requests(state="closed")

            # One of our repos had no prs, for some reason this caused the program to crash
            # There may be a better way to handle this
            try:
                prs.next()
            except NotFoundError:
                continue
            for pr in prs:
                merge_date = pr.merged_at.replace(tzinfo=None)
                if pr.merged_at and q_start <= merge_date <= q_end:

                    print(repo.name, pr.created_at, pr.title)

                    pr_date = pr.created_at.replace(tzinfo=None)

                    full_pr = repo.pull_request(pr.number)

                    total_diff = full_pr.additions_count + full_pr.deletions_count
                    print('total diff', total_diff)

                    diff_after_pr = 0
                    for c in pr.commits():
                        commit_json = c.as_dict()
                        commit_datetime = datetime.strptime(commit_json['commit']['author']['date'].replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
                        if commit_datetime < pr_date:
                            continue

                        for f in repo.commit(c.sha).files:
                            diff_after_pr += f['additions'] + f['deletions']

                    print('diff after PR', diff_after_pr)
                    print('total effort rework: {0:.2f}%'.format((diff_after_pr / total_diff) * 100))
                    i += 1
                break
            if i > 10:
                break
        return []
