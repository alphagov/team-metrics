import pytest
from app.source.github import Github
from app.daos.dao_git_metric import dao_upsert_git_metric
from github3.exceptions import NotFoundError
from datetime import datetime


def mock_github_client(mocker, prs_dict=None, no_prs=False, create_date=datetime(2018, 12, 14), commit_dates_arr=None):

    if not commit_dates_arr:
        commit_dates_arr = [
            "2018-12-10T12:12:12",
            "2018-12-11T12:12:12",
            "2018-12-12T12:12:12",
            "2018-12-13T12:12:12",
            "2018-12-14T12:12:12",
        ]

    class MockGithubClient:
        def __init__(self, token=''):
            self.token = token

        def search_repositories(self, query):
            return [Repository()]

    class Repository:
        def __init__(self):
            self.repository = Repo()
            pass

    class Repo:
        url = "https://github.com/alphagov/test_repo_name"

        def __init__(self, arg=1):
            self.name = "test_repo_name"

        def pull_request(self, number):
            return PullReq()

        def pull_requests(self, state):
            return PullReqs()

        def commit(self, sha):
            return RepoCommit()

    class RepoCommit:
        files = [{
            'additions': 20,
            'deletions': 10
        }]

        def __init__(self):
            pass

    class PullReq:
        comments_count = 0
        review_comments_count = 4

        def __init__(self, number=None, title=None, created_at=None, merged_at=None):
            self.number = number
            self.title = title
            self.created_at = created_at
            self.merged_at = merged_at

        def commits(self):
            return Commits()

    # need to create something similar to prs_dict for commits
    if prs_dict is None:
        prs_dict = [
            {
                'number': 1,
                'title': 'test 1',
                'created_at': datetime(2018, 11, 1, 12, 0),
                'merged_at': datetime(2018, 11, 2, 12, 0)
            },
            {
                'number': 2,
                'title': 'test 2',
                'created_at': datetime(2018, 11, 3, 12, 0),
                'merged_at': datetime(2018, 11, 4, 12, 0)
            }
        ]

    prs = []

    for pr in prs_dict:
        # ** unpacks a dict as key-value
        prs.append(PullReq(**pr))

    class PullReqs:
        number = 10
        title = "mock_title"
        _prs = prs

        def __init__(self):
            self.created_at = create_date
            self.no_prs = no_prs
            self.low = 0
            self.high = len(prs)
            self.merged_at = datetime(2018, 12, 16)

        def __iter__(self):
            return self

        def next(self):
            if self.no_prs:
                raise NotFoundError(Thing())
            elif self.low < self.high:
                pr = self._prs[self.low]
                self.low += 1
                return pr
            else:
                raise StopIteration

        __next__ = next

    class Commits:
        sha = "mock"

        def __init__(self):
            self.low = 0
            self.high = len(commit_dates_arr) - 1

        def __iter__(self):
            return self

        def next(self):
            if self.low < self.high:
                self.low += 1
                # should not return self but rather the RepoCommit obj with relevant parts
                return self
            else:
                raise StopIteration

        __next__ = next

        # should be in RepoCommit not in this class
        def as_dict(self):
            return {
                'commit': {
                    'author': {
                        'date': commit_dates_arr[self.low]
                    }
                },
            }

    class Thing:
        status_code = 400
        content = "hello"

        def __init__(self):
            pass

    mocker.patch("os.environ", {
        "TM_TEAM_ID": "1",
        "TM_GITHUB_PAT": "test pat"
    })
    mocker.patch.object(Github, "gh_login", return_value=MockGithubClient())
    mocker.patch("app.source.github.get_team_profile", return_value={"repos": "test_repo", "name": "fake name"})


def test_just_get_git_metrics(mocker):
    prs_dict = [
        {
            'number': 1,
            'title': 'test 1',
            'created_at': datetime(2018, 12, 14, 12, 0),
            'merged_at': datetime(2018, 12, 16, 12, 0)
        },
    ]

    mock_github_client(mocker, prs_dict=prs_dict)
    dao_mock = mocker.patch("app.source.github.dao_upsert_git_metric")

    Github().get_metrics(year=2018, quarter=3)
    dao_mock.assert_called_once_with({
        'team_id': '1',
        'team_name': 'fake name',
        'name': 'test_repo_name',
        'pr_number': prs_dict[0]['number'],
        # would be better to get the dates from the prs_dict rather than hard code it
        'start_date': '2018-12-14',
        'end_date': '2018-12-16',
        'diff_count': 30,
        'total_diff_count': 120,
        'comments_count': 4})
    # assert False


def test_get_git_metrics_only_in_quarter(mocker):
    mock_github_client(mocker)
    dao_mock = mocker.patch("app.source.github.dao_upsert_git_metric")

    Github().get_metrics(year=2018, quarter=2)
    dao_mock.assert_not_called()


def test_get_git_metrics_includes_prs_started_before_quarter(mocker):
    prs_dict = [
        {
            'number': 1,
            'title': 'test 1',
            'created_at': datetime(2018, 12, 8, 12, 0),
            'merged_at': datetime(2018, 12, 16, 12, 0)
        },
    ]

    date = datetime(2018, 12, 8)
    mock_github_client(mocker, create_date=date, prs_dict=prs_dict)
    dao_mock = mocker.patch("app.source.github.dao_upsert_git_metric")

    Github().get_metrics(year=2018, quarter=3)
    dao_mock.assert_called_once_with({
        'team_id': '1',
        'team_name': 'fake name',
        'name': 'test_repo_name',
        'pr_number': prs_dict[0]['number'],
        'start_date': "2018-12-08",
        'end_date': "2018-12-16",
        'diff_count': 120,
        'total_diff_count': 120,
        'comments_count': 4})


def test_get_git_metrics_ignores_repos_without_prs(mocker):
    mock_github_client(mocker, no_prs=True)
    dao_mock = mocker.patch("app.source.github.dao_upsert_git_metric")

    Github().get_metrics(year=2018, quarter=3)
    dao_mock.assert_not_called()
