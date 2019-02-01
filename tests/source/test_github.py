import pytest
from app.source.github import Github
from app.daos.dao_git_metric import dao_upsert_git_metric
from github3.exceptions import NotFoundError
from datetime import datetime


def mock_github_client(mocker, prs_dict=None, commit_dates_arr=None):
    if not commit_dates_arr:
        commit_dates_arr = [
            {
                'date': "2018-12-10T12:12:12",
                'files': [{'additions': 20, 'deletions': 10}]
            },
            {
                'date': "2018-12-11T12:12:12",
                'files': [{'additions': 20, 'deletions': 10}]
            },
            {
                'date': "2018-12-12T12:12:12",
                'files': [{'additions': 20, 'deletions': 10}]
            },
            {
                'date': "2018-12-13T12:12:12",
                'files': [{'additions': 20, 'deletions': 10}]
            },
            {
                'date': "2018-12-14T12:12:12",
                'files': [{'additions': 20, 'deletions': 10}]
            }
        ]

    class PullReq:
        def __init__(
            self,
            state='closed',
            number=None,
            title=None,
            created_at=None,
            merged_at=None,
            comments_count=None,
            review_comments_count=None
        ):
            self.number = number
            self.title = title
            self.created_at = created_at
            self.merged_at = merged_at
            self.comments_count = comments_count
            self.review_comments_count = review_comments_count

        def commits(self):
            return Commits()

    if prs_dict is None:
        prs_dict = [
            {
                'number': 1,
                'title': 'test 1',
                'created_at': datetime(2018, 12, 14, 12, 0),
                'merged_at': datetime(2018, 12, 16, 12, 0),
                'comments_count': 0,
                'review_comments_count': 4
            },
            {
                'number': 2,
                'title': 'test 2',
                'created_at': datetime(2017, 11, 3, 12, 0),
                'merged_at': datetime(2017, 11, 4, 12, 0),
                'comments_count': 0,
                'review_comments_count': 4
            }
        ]

    prs = []

    for pr in prs_dict:
        # ** unpacks a dict as key-value
        prs.append(PullReq(**pr))

    class Commit:
        def __init__(self, date=None, files=None):
            self.sha = date
            self.files = files

        def as_dict(self):
            return {
                'commit': {
                    'author': {
                        'date': self.sha
                    }
                },
            }

    commits = []

    for date in commit_dates_arr:
        commits.append(Commit(**date))

    class MockGithubClient:
        def __init__(self, token=''):
            self.token = token

        def search_repositories(self, query):
            return [Repository()]

    class Repository:
        def __init__(self):
            self.repository = Repo()

    class Repo:
        url = "https://github.com/alphagov/test_repo_name"

        def __init__(self, arg=1):
            self.name = "test_repo_name"

        def pull_request(self, number):
            for request in PullReqs():
                if request.number == number:
                    return request

        def pull_requests(self, state):
            return PullReqs()

        def commit(self, sha):
            for commit in PullReq().commits():
                if commit.sha == sha:
                    return commit

    class PullReqs:
        _prs = prs

        def __init__(self):
            self.counter = 0

        def __iter__(self):
            return self

        def next(self):
            if self._prs == []:
                raise NotFoundError(Thing())
            elif self.counter < len(prs):
                self.counter += 1
                return self._prs[self.counter - 1]
            else:
                raise StopIteration

        __next__ = next

    class Commits:
        _commits = commits

        def __init__(self):
            self.counter = 0

        def __iter__(self):
            return self

        def next(self):
            if self.counter < len(commit_dates_arr):
                self.counter += 1
                return self._commits[self.counter - 1]
            else:
                raise StopIteration

        __next__ = next

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


def test_get_git_metrics(mocker):
    mock_github_client(mocker)
    dao_mock = mocker.patch("app.source.github.dao_upsert_git_metric")

    Github().get_metrics(year=2018, quarter=3)
    dao_mock.assert_called_once_with({
        'team_id': '1',
        'team_name': 'fake name',
        'name': 'test_repo_name',
        'pr_number': 1,
        'start_date': "2018-12-14",
        'end_date': "2018-12-16",
        'diff_count': 30,
        'total_diff_count': 150,
        'comments_count': 4})


def test_get_git_metrics_only_in_quarter(mocker):
    mock_github_client(mocker)
    dao_mock = mocker.patch("app.source.github.dao_upsert_git_metric")

    Github().get_metrics(year=2018, quarter=2)
    dao_mock.assert_not_called()


def test_get_git_metrics_includes_prs_started_before_quarter(mocker):
    pr_opened_before_quarter = [
        {
            'number': 1,
            'title': 'test 1',
            'created_at': datetime(2017, 12, 14, 12, 0),
            'merged_at': datetime(2018, 12, 16, 12, 0),
            'comments_count': 0,
            'review_comments_count': 4
        },
    ]
    mock_github_client(mocker, prs_dict=pr_opened_before_quarter)
    dao_mock = mocker.patch("app.source.github.dao_upsert_git_metric")

    Github().get_metrics(year=2018, quarter=3)
    dao_mock.assert_called_once_with({
        'team_id': '1',
        'team_name': 'fake name',
        'name': 'test_repo_name',
        'pr_number': 1,
        'start_date': "2017-12-14",
        'end_date': "2018-12-16",
        'diff_count': 150,
        'total_diff_count': 150,
        'comments_count': 4})


def test_get_git_metrics_ignores_repos_without_prs(mocker):
    mock_github_client(mocker, prs_dict=[{}])
    dao_mock = mocker.patch("app.source.github.dao_upsert_git_metric")
    Github().get_metrics(year=2018, quarter=3)
    dao_mock.assert_not_called()
