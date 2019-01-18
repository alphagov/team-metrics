import os
from datetime import datetime, timedelta

from github3 import login
from github3.exceptions import NotFoundError

import yaml

from app.metrics import Metrics
from app.source import Base, get_quarter_daterange

from app.daos.dao_git_metric import dao_upsert_git_metric


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
        q_start, q_end = get_quarter_daterange(year, quarter)
        repos_yml = None

        with open('git-repos.yml') as f:
            repos_yml = yaml.load(f)

        org = self.gh.organization("alphagov")
        repositories = org.team(os.getenv("TM_GITHUB_TEAM_ID")).repositories()
        for repo in repositories:
            if repo.name not in repos_yml['observe']['repos'].split(' '):
                continue

            prs = repo.pull_requests(state="closed")

            # One of our repos had no prs, for some reason this caused the program to crash
            # There may be a better way to handle this
            try:
                prs.next()
            except NotFoundError:
                continue

            for pr in prs:
                # if repo.url == 'https://api.github.com/repos/alphagov/prometheus-aws-configuration-beta' and pr.number == 259:
                #     import pdb; pdb.set_trace()
                # else:
                #     continue

                if pr.merged_at and q_start <= pr.merged_at.replace(tzinfo=None) <= q_end:
                    print(repo.name, pr.created_at, pr.title)

                    pr_date = pr.created_at.replace(tzinfo=None)

                    diff_before_pr = diff_after_pr = 0
                    for c in pr.commits():
                        commit_json = c.as_dict()
                        commit_datetime = datetime.strptime(commit_json['commit']['author']['date'].replace("Z", ""), "%Y-%m-%dT%H:%M:%S")

                        for f in repo.commit(c.sha).files:
                            if commit_datetime < pr_date:
                                diff_before_pr += f['additions'] + f['deletions']
                            else:
                                diff_after_pr += f['additions'] + f['deletions']

                    total_diff = diff_before_pr + diff_after_pr
                    if total_diff == 0:
                        rework = 0
                    else:
                        rework = (diff_after_pr / total_diff) * 100
                    print('total diff', total_diff)
                    print('diff after PR', diff_after_pr)
                    print('total effort rework: {0:.2f}%'.format(rework))

                    full_pr = repo.pull_request(pr.number)

                    dao_upsert_git_metric({
                        'team_id': os.getenv("TM_GITHUB_TEAM_ID"),
                        'repo_url': repo.html_url,
                        'pr_number': pr.number,
                        'start_date': pr.created_at,
                        'end_date': pr.merged_at,
                        'diff_count': diff_after_pr,
                        'total_diff_count': total_diff,
                        'comments_count': full_pr.comments_count,
                    })
                    
                    i += 1
                # break
            # if i > 10:
            #     break
        print(f'Number upserted: {i}')
