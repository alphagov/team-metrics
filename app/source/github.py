import os
from datetime import datetime, timedelta

from github3 import login

from app.metrics import Metrics
from app.source import Base


class Github(Base):
    def __init__(self):
        self.gh = login(token=os.environ['TM_GITHUB_PAT'])

    # collect metrics on repos for which github user has been added to as a contributor
    # record number of changes to the files on master and number of commits since 2 weeks
    def get_metrics(self):
        i = 0
        login_filter = self.gh.me().login

        since = datetime.today() - timedelta(weeks=2)
        since = since.strftime('%Y-%m-%d')
        for org in self.gh.organizations():
            print("Processing {} repos".format(org.url))
            for repo in org.repositories():
                contributor_logins = [l.login for l in repo.contributors()]

                if "master" not in [b.name for b in repo.branches()]:
                    print("No master in {}".format(repo.name))
                    continue

                master = repo.branch("master")

                r = self.gh.repository(repo.owner, repo.name)
                commits = r.commits(sha=master.commit.sha, since=since)

                if commits and login_filter in contributor_logins and not r.archived:
                    files = {}
                    print("\n{} {} since {}".format(master.url, master.commit.sha, since))

                    for c in commits:
                        for f in r.commit(c.sha).files:
                            filename = f['filename']
                            activity = files.get(filename)

                            if not activity:
                                activity = {
                                    'additions': f['additions'],
                                    'deletions': f['deletions'],
                                    'changes': f['changes'],
                                    'num_commits': 0
                                }
                            else:
                                activity = {
                                    'additions': f['additions'] + activity['additions'],
                                    'deletions': f['deletions'] + activity['deletions'],
                                    'changes': f['changes'] + activity['changes'],
                                    'num_commits': activity['num_commits'] + 1
                                }
                            files[filename] = activity

                    if files:
                        for k, v in sorted(files.items(), key=lambda k: k[1]['num_commits'], reverse=True):
                            print("  {}: {}".format(k, files[k]))
                    else:
                        print("  no commits on master")
                    if i > 5: break  # don't process other repos
                    i += 1
                else:
                    print('.', end='', flush=True)
            break  # don't process other orgs
