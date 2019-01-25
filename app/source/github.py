import os
from datetime import datetime, timedelta

from github3 import login
from github3.exceptions import NotFoundError

import yaml

from app.metrics import Metrics
from app.source import Base, NotFound, get_quarter_daterange

from app.daos.dao_git_metric import dao_upsert_git_metric


class Github(Base):
    def __init__(self, team_id=None):
        self.team_id = team_id if team_id else os.getenv("TM_GITHUB_TEAM_ID")

        self.gh = login(token=os.environ['TM_GITHUB_PAT'])

    def get_metrics(self, year=None, quarter=None):
        i = 0
        q_start, q_end = get_quarter_daterange(year, quarter)

        with open('teams.yml') as f:
            teams_yml = yaml.load(f)

        team = [t for t in teams_yml['teams'] if str(t.get('id')) == self.team_id]

        if not team:
            raise NotFound(f"Team id {self.team_id} not found in teams.yml")

        for yml_repo in team[0]['repos'].split(' '):
            search_results = self.gh.search_repositories(query=f'archived:false org:alphagov {yml_repo} in:name')

            for repo in [r.repository for r in search_results]:
                prs = repo.pull_requests(state="closed")

                # One of our repos had no prs, for some reason this caused the program to crash
                # There may be a better way to handle this
                try:
                    prs.next()
                except NotFoundError:
                    continue

                for pr in prs:
                    # if repo.name == 'prometheus-aws-configuration-beta' and pr.number == 190:
                    #     import pdb; pdb.set_trace()
                    # else:
                    #     continue

                    if pr.merged_at and q_start <= pr.merged_at.replace(tzinfo=None) <= q_end:
                        print(repo.name, pr.title, pr.number)

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
                        rework = (diff_after_pr / total_diff) * 100 if total_diff > 0 else 0
                        print('total diff', total_diff)
                        print('diff after PR', diff_after_pr)
                        print('total effort rework: {0:.2f}%'.format(rework))

                        full_pr = repo.pull_request(pr.number)

                        dao_upsert_git_metric({
                            'team_id': self.team_id,
                            'name': repo.name,
                            'pr_number': pr.number,
                            'start_date': pr.created_at,
                            'end_date': pr.merged_at,
                            'diff_count': diff_after_pr,
                            'total_diff_count': total_diff,
                            'comments_count': full_pr.comments_count + full_pr.review_comments_count,
                        })
                        
                        i += 1
                    # break
                # if i > 10:
                #     break
        print(f'Number upserted: {i}')
