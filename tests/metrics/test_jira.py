from datetime import timedelta

from freezegun import freeze_time

from app.source import get_datetime, get_process_cycle_efficiency
from app.source.jira import Jira


def mock_issue(_histories=None):
    if not _histories:
        _histories = [
            {
                'created': '2018-11-01',
                'toString': 'In Progress'
            }
        ]

    class MockIssue:
        class MockChangelog:
            class MockHistory:
                class MockItem:
                    field = 'status'

                    def __init__(self, history):
                        self.toString = history['toString']
                        self.fromString = history['fromString']

                def __init__(self, history):
                    self.created = history['created']
                    self.items = [
                        self.MockItem(history)
                    ]

            histories = []
            for history in _histories:
                if not history.get('fromString'):
                    history['fromString'] = ''
                histories.append(MockHistory(history))

        id = 'id'
        changelog = MockChangelog()

        def __init__(self):
            pass

    return MockIssue()


def mock_jira_client(mocker, issue):
    mocker.patch("os.environ", {
        'TM_JIRA_USER': 'test_user@gov.uk',
        'TM_JIRA_PAT': 'test_pat',
        'TM_JIRA_HOST': 'jira.host',
    })

    mocker.patch("jira.resources.GreenHopperResource.AGILE_BASE_REST_PATH", "agile/path")

    class MockJiraClient:
        class MockProject:
            key = 'test_project'
            id = None

        class MockBoard:
            id = None

        class MockSprint:
            id = None
            name = 'test_sprint'
            raw = {
                'startDate': '2018-11-01T12:00:00',
                'endDate': '2018-11-08T12:00:00',
                'state': None
            }

        def __init__(self, basic_auth=None, server=None, options=None):
            pass

        def issue(self, _, **__):
            return issue

        def projects(self):
            return [
                self.MockProject()
            ]

        def boards(self, **__):
            return [
                self.MockBoard()
            ]

        def sprints(self, *_):
            return [
                self.MockSprint()
            ]

        def search_issues(self, *_):
            return [issue]

    mocker.patch("app.source.jira.JIRA", MockJiraClient)


def test_jira_get_cycle_time(mocker):
    issue = mock_issue(
        [
            {
                'created': '2018-11-01T12:00:00',
                'toString': 'In Progress'
            },
            {
                'created': '2018-11-02T12:00:00',
                'toString': 'Done'
            },
        ]
    )

    mock_jira_client(mocker, issue)

    j = Jira()

    assert str(j.get_cycle_time(issue)) == '1 day, 0:00:00'


def test_get_cycle_time_is_None_if_not_done(mocker):
    issue = mock_issue(
        [
            {
                'created': '2018-11-01T12:00:00',
                'toString': 'In Progress'
            },
            {
                'created': '2018-11-02T12:00:00',
                'toString': 'Blocked'
            },
        ]
    )

    mock_jira_client(mocker, issue)

    j = Jira()

    assert not j.get_cycle_time(issue)


def test_get_cycle_time_allows_blocked(mocker):
    issue = mock_issue(
        [
            {
                'created': '2018-11-01T12:00:00',
                'toString': 'In Progress'
            },
            {
                'created': '2018-11-02T12:00:00',
                'toString': 'Blocked'
            },
            {
                'created': '2018-11-05T12:00:00',
                'toString': 'Done'
            },
        ]
    )

    mock_jira_client(mocker, issue)

    j = Jira()

    assert str(j.get_cycle_time(issue)) == '2 days, 0:00:00'


def test_jira_get_blocked_time(mocker):
    issue = mock_issue(
        [
            {
                'created': '2018-11-01T12:00:00',
                'toString': 'In Progress'
            },
            {
                'created': '2018-11-02T12:00:00',
                'toString': 'Blocked'
            },
            {
                'created': '2018-11-05T12:00:00',
                'fromString': 'Blocked',
                'toString': 'In Progress'
            },
            {
                'created': '2018-11-06T12:00:00',
                'toString': 'Done'
            },
        ]
    )

    mock_jira_client(mocker, issue)

    j = Jira()

    assert str(j.get_blocked_time(issue)) == '1 day, 0:00:00'


def test_get_blocked_time_is_None_if_not_blocked(mocker):
    issue = mock_issue(
        [
            {
                'created': '2018-11-01T12:00:00',
                'toString': 'In Progress'
            },
            {
                'created': '2018-11-05T12:00:00',
                'toString': 'Done'
            },
        ]
    )

    mock_jira_client(mocker, issue)

    j = Jira()

    assert not j.get_blocked_time(issue)


def test_get_blocked_time_is_None_if_still_blocked(mocker):
    issue = mock_issue(
        [
            {
                'created': '2018-11-01T12:00:00',
                'toString': 'In Progress'
            },
            {
                'created': '2018-11-05T12:00:00',
                'toString': 'Blocked'
            },
        ]
    )

    mock_jira_client(mocker, issue)

    j = Jira()

    assert not j.get_blocked_time(issue)


def test_jira_get_metrics(mocker):
    history = [
        {
            'created': '2018-11-01T12:00:00',
            'toString': 'In Progress'
        },
        {
            'created': '2018-11-02T12:00:00',
            'toString': 'Done'
        },
    ]

    issue = mock_issue(history)

    mock_jira_client(mocker, issue)

    j = Jira(project_id='test_project')
    metrics = j.get_metrics()

    assert len(metrics) == 1
    assert metrics[0].avg_cycle_time == (
        get_datetime(history[1]['created']) - get_datetime(history[0]['created'])).total_seconds()
    assert metrics[0].process_cycle_efficiency == 1


@freeze_time("2018-12-01 12:00:00")
def test_get_jira_metrics_for_last_12_weeks(mocker):
    history = [
        {
            'created': '2018-11-01T12:00:00',
            'toString': 'In Progress'
        },
        {
            'created': '2018-11-02T12:00:00',
            'toString': 'Done'
        },
    ]

    issue = mock_issue(history)

    mock_jira_client(mocker, issue)

    j = Jira(project_id='test_project')
    metrics = j.get_metrics(last_num_weeks=12)

    assert len(metrics) == 1
    assert metrics[0].avg_cycle_time == (
        get_datetime(history[1]['created']) - get_datetime(history[0]['created'])).total_seconds()
    assert metrics[0].process_cycle_efficiency == 1


@freeze_time("2018-12-01 12:00:00")
def test_get_no_metrics_for_last_2_weeks(mocker):
    history = [
        {
            'created': '2018-11-01T12:00:00',
            'toString': 'In Progress'
        },
        {
            'created': '2018-11-02T12:00:00',
            'toString': 'Done'
        },
    ]

    issue = mock_issue(history)

    mock_jira_client(mocker, issue)

    j = Jira(project_id='test_project')
    metrics = j.get_metrics(last_num_weeks=2)

    assert not metrics


def test_get_jira_metrics_with_blocker(mocker):
    history = [
        {
            'created': '2018-11-01T12:00:00',
            'toString': 'In Progress'
        },
        {
            'created': '2018-11-02T12:00:00',
            'toString': 'Blocked'
        },
        {
            'created': '2018-11-05T12:00:00',
            'fromString': 'Blocked',
            'toString': 'In Progress'
        },
        {
            'created': '2018-11-06T12:00:00',
            'toString': 'Done'
        },
    ]

    issue = mock_issue(history)

    mock_jira_client(mocker, issue)

    j = Jira(project_id='test_project')
    metrics = j.get_metrics()

    cycle_time_timedelta = get_datetime(history[3]['created']) - get_datetime(history[0]['created']) - timedelta(days=2)

    assert len(metrics) == 1
    assert metrics[0].avg_cycle_time == cycle_time_timedelta.total_seconds()
    assert metrics[0].process_cycle_efficiency == (
        (
            cycle_time_timedelta - (
                get_datetime(history[2]['created']) - get_datetime(history[1]['created']) - timedelta(days=2))
        ) / cycle_time_timedelta
    )


def test_get_jira_metrics_is_none_if_not_done(mocker):
    history = [
        {
            'created': '2018-11-01T12:00:00',
            'toString': 'In Progress'
        },
        {
            'created': '2018-11-02T12:00:00',
            'toString': 'Blocked'
        },
    ]

    issue = mock_issue(history)

    mock_jira_client(mocker, issue)

    j = Jira(project_id='test_project')
    metrics = j.get_metrics()

    assert len(metrics) == 1
    assert metrics[0].num_completed == 0
    assert metrics[0].num_incomplete == 1
