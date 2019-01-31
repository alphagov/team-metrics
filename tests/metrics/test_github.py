from app.source.github import Github
from app.daos.dao_git_metric import dao_upsert_git_metric
from github3.exceptions import NotFoundError
import datetime


def mock_github_client(mocker, no_prs=False, create_date=datetime.datetime(2018, 12, 14)):
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

        def __init__(self):
            pass

    class PullReqs:
        number = 10
        title = "mock_title"

        def __init__(self, state='closed', low=0, high=1):
            self.created_at = create_date
            self.no_prs = no_prs
            self.low = low
            self.high = high
            if state == 'closed':
                self.merged_at = datetime.datetime(2018, 12, 16)

        def __iter__(self):
            return self

        def next(self):
            if self.low <= self.high:
                print(f"self: {self.low}")
                self.low += 1
                return self
            elif self.no_prs:
                raise NotFoundError(Thing())
            else:
                raise StopIteration

        def commits(self):
            return Commits()

        __next__ = next

    class Commits:
        sha = "mock"

        def __init__(self, low=0, high=3):
            self.low = low
            self.high = high

        def __iter__(self):
            return self

        def next(self):
            if self.low <= self.high:
                print(f"self_commit: {self.low}")
                self.low += 1
                return self
            else:
                raise StopIteration

        __next__ = next

        def as_dict(self):
            return {
                'commit': {
                    'author': {
                        'date': "2018-12-%sT12:12:12" % (10 + self.low)
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


def test_get_git_metrics(mocker):
    mock_github_client(mocker)
    dao_mock = mocker.patch("app.source.github.dao_upsert_git_metric")

    Github().get_metrics(year=2018, quarter=3)
    dao_mock.assert_called_once_with({
        'team_id': '1',
        'team_name': 'fake name',
        'name': 'test_repo_name',
        'pr_number': 10,
        'start_date': "2018-12-14",
        'end_date': "2018-12-16",
        'diff_count': 30,
        'total_diff_count': 120,
        'comments_count': 4})


def test_get_git_metrics_only_in_quarter(mocker):
    mock_github_client(mocker)
    dao_mock = mocker.patch("app.source.github.dao_upsert_git_metric")

    Github().get_metrics(year=2018, quarter=2)
    dao_mock.assert_not_called()


def test_get_git_metrics_includes_prs_started_before_quarter(mocker):
    date = datetime.datetime(2018, 12, 8)
    mock_github_client(mocker, create_date=date)
    dao_mock = mocker.patch("app.source.github.dao_upsert_git_metric")

    Github().get_metrics(year=2018, quarter=3)
    dao_mock.assert_called_once_with({
        'team_id': '1',
        'team_name': 'fake name',
        'name': 'test_repo_name',
        'pr_number': 10,
        'start_date': "2018-12-08",
        'end_date': "2018-12-16",
        'diff_count': 120,
        'total_diff_count': 120,
        'comments_count': 4})


def test_get_git_metrics_ignores_repos_without_prs(mocker):
    mock_github_client(mocker, no_prs=True)
    dao_mock = mocker.patch("app.source.github.dao_upsert_git_metric")

    try:
        Github().get_metrics(year=2018, quarter=3)
    except NotFoundError:
        pass
