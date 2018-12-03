from team_metrics.source import get_datetime, get_process_cycle_efficiency
from team_metrics.source.jira import Jira


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
                'startDate': None,
                'endDate': None,
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

    mocker.patch("team_metrics.source.jira.JIRA", MockJiraClient)


def test_get_cycle_time(mocker):
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
                'created': '2018-11-03T12:00:00',
                'toString': 'Done'
            },
        ]
    )

    mock_jira_client(mocker, issue)

    j = Jira()

    assert str(j.get_cycle_time(issue)) == '2 days, 0:00:00'


def test_get_blocked_time(mocker):
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
                'created': '2018-11-03T12:00:00',
                'fromString': 'Blocked',
                'toString': 'In Progress'
            },
            {
                'created': '2018-11-04T12:00:00',
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
                'created': '2018-11-04T12:00:00',
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
                'created': '2018-11-04T12:00:00',
                'toString': 'Blocked'
            },
        ]
    )

    mock_jira_client(mocker, issue)

    j = Jira()

    assert not j.get_blocked_time(issue)


def test_get_metrics(mocker):
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
    assert metrics[0].cycle_time == get_datetime(history[1]['created']) - get_datetime(history[0]['created'])
    assert metrics[0].process_cycle_efficiency == 1


def test_get_metrics_with_blocker(mocker):
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
            'created': '2018-11-03T12:00:00',
            'fromString': 'Blocked',
            'toString': 'In Progress'
        },
        {
            'created': '2018-11-04T12:00:00',
            'toString': 'Done'
        },
    ]

    issue = mock_issue(history)

    mock_jira_client(mocker, issue)

    j = Jira(project_id='test_project')
    metrics = j.get_metrics()

    assert len(metrics) == 1
    assert metrics[0].cycle_time == get_datetime(history[3]['created']) - get_datetime(history[0]['created'])
    assert metrics[0].process_cycle_efficiency == (
        (
            metrics[0].cycle_time - (get_datetime(history[2]['created']) - get_datetime(history[1]['created']))
        ) / metrics[0].cycle_time
    )


def test_get_metrics_is_none_if_not_done(mocker):
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
    assert metrics[0].num_stories == 0
    assert metrics[0].num_incomplete == 1
