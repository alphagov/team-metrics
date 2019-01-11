import pytest
import uuid

from app.source import get_datetime
from app.source.trello import Trello


def mock_trello_client(mocker, lists=None):
    mocker.patch("os.environ", {
        'TM_TRELLO_TOKEN': 'test_token',
        'TM_TRELLO_PAT': 'test_pat',
        'TM_TRELLO_ORG_ID': 'test_org',
        'TM_TRELLO_BOARD_ID': 'test_board',
    })

    class MockList:
        id = '1'
        name = 'test_list'
        cards = []
        closed = False

        def __init__(self, name, cards=None):
            self.name = name

            if cards:
                self.cards = cards
            elif not lists:
                self.cards.append(MockCard())

        def list_cards(self):
            return self.cards

    class MockCard:
        def __init__(self, name='test_card', description=None, movements=None, created_date=None):
            self.id = uuid.uuid1()
            self.name = name
            self.description = description
            self.movements = movements
            self.created_date = created_date

        def list_movements(self):
            return self.movements

    class MockTrelloClient:
        class MockBoard:
            name = 'test_board'

            def list_lists(self):
                return _lists

        def __init__(self, api_key=None, token=None, lists=None):
            pass

        def get_board(self, board_id):
            return self.MockBoard()

    if not lists:
        _lists = [
            MockList(
                'TM Q3 sprints',
                cards=[
                    MockCard('Done (week 1)', description='2018-11-28 - 2018-12-11')
                ]
            ),
            MockList(
                'Done (week 1)',
                cards=[
                    MockCard(
                        'test_card',
                        movements=[
                            {
                                'datetime': '2018-12-01',
                                'source': {
                                    'name': 'test_source_name'
                                },
                                'destination': {
                                    'name': 'test_destination_name'
                                }
                            }
                        ],
                        created_date='2019-01-07T12:00:00'
                    )
                ]
            )
        ]
    else:
        _lists = []
        for _list in lists:
            cards = []
            for card in _list['cards']:
                movements = []
                if card.get('movements'):
                    for movement in card.get('movements'):
                        movements.append({
                            'datetime': get_datetime(movement['datetime']),
                            'source': {
                                'name': movement['source']
                            },
                            'destination': {
                                'name': movement['destination']
                            }
                        })

                cards.append(
                    MockCard(
                        card['name'],
                        description=card.get('description'),
                        movements=movements,
                        created_date=card.get('created_date')
                    )
                )
            _lists.append(MockList(_list['name'], cards))

    mocker.patch("app.source.trello.TrelloClient", MockTrelloClient)


def test_trello_get_metrics(mocker):
    sprint_name = 'Done (week 1)'
    lists = [
        {
            'name': 'TM Q3 sprints',
            'cards': [
                {
                    'name': sprint_name,
                    'description': '2019-01-07 - 2019-01-13'
                }
            ]
        },
        {
            'name': sprint_name,
            'cards': [
                {
                    'name': 'card done',
                    'movements': [
                        {
                            'datetime': '2019-01-07T12:00:00',
                            'source': 'Backlog',
                            'destination': 'Sprint 1 - TO DO'
                        },
                        {
                            'datetime': '2019-01-07T12:00:00',
                            'source': 'Sprint 1 - TO DO',
                            'destination': 'In Progress'
                        },
                        {
                            'datetime': '2019-01-08T12:00:00',
                            'source': 'In Progress',
                            'destination': 'Blocked'
                        },
                        {
                            'datetime': '2019-01-08T12:00:00',
                            'source': 'Blocked',
                            'destination': 'Sign off'
                        },
                        {
                            'datetime': '2019-01-08T13:00:00',
                            'source': 'Sign off',
                            'destination': sprint_name
                        }
                    ]
                }
            ]
        }
    ]

    mock_trello_client(mocker, lists=lists)

    t = Trello()
    metrics = t.get_metrics()

    assert len(metrics) == 1
    assert metrics[0].num_completed == 1
    assert metrics[0].process_cycle_efficiency == 1


def test_multi_sign_off_entries(mocker):
    sprint_name = 'Done (week 1)'
    lists = [
        {
            'name': 'TM Q3 sprints',
            'cards': [
                {
                    'name': sprint_name,
                    'description': '2019-01-07 - 2019-01-13'
                }
            ]
        },
        {
            'name': sprint_name,
            'cards': [
                {
                    'name': 'card done',
                    'movements': [
                        {
                            'datetime': '2019-01-08T10:00:00',
                            'source': 'Backlog',
                            'destination': 'Sprint 1 - TO DO'
                        },
                        {
                            'datetime': '2019-01-08T11:00:00',
                            'source': 'Sprint 1 - TO DO',
                            'destination': 'In Progress'
                        },
                        {
                            'datetime': '2019-01-08T12:00:00',
                            'source': 'In Progress',
                            'destination': 'Sign off'
                        },
                        {
                            'datetime': '2019-01-08T13:00:00',
                            'source': 'Sign off',
                            'destination': 'In Progress'
                        },
                        {
                            'datetime': '2019-01-08T14:00:00',
                            'source': 'In Progress',
                            'destination': 'Sign off'
                        },
                        {
                            'datetime': '2019-01-08T15:00:00',
                            'source': 'Sign off',
                            'destination': sprint_name
                        }
                    ]
                }
            ]
        }
    ]

    mock_trello_client(mocker, lists=lists)

    t = Trello()
    metrics = t.get_metrics()

    assert len(metrics) == 1
    assert metrics[0].num_completed == 1
    assert metrics[0].process_cycle_efficiency == 1
    assert metrics[0].avg_cycle_time == 7200


@pytest.mark.parametrize('list_name', [
    'In Progress', 'Blocked'
])
def test_trello_get_incomplete_stories(mocker, list_name):
    sprint_name = 'Done (week 1)'

    lists = [
        {
            'name': 'TM Q3 sprints',
            'cards': [
                {
                    'name': sprint_name,
                    'description': '2019-01-07 - 2019-01-13'
                }
            ]
        },
        {
            'name': sprint_name,
            'cards': []
        },
        {
            'name': list_name,
            'cards': [
                {
                    'name': 'card completed',
                    'movements': [
                        {
                            'datetime': '2019-01-07T12:00:00',
                            'source': 'Backlog',
                            'destination': 'Sprint 1 - TO DO'
                        },
                        {
                            'datetime': '2019-01-07T12:00:00',
                            'source': 'Sprint 1 - TO DO',
                            'destination': list_name
                        }
                    ]
                }
            ]
        }
    ]

    mock_trello_client(mocker, lists=lists)

    t = Trello()
    metrics = t.get_metrics()

    assert len(metrics) == 1
    assert metrics[0].num_completed == 0
    assert metrics[0].num_incomplete == 1


def test_trello_get_incomplete_stories_not_moved(mocker):
    sprint_name = 'Done (week 1)'

    lists = [
        {
            'name': 'TM Q3 sprints',
            'cards': [
                {
                    'name': sprint_name,
                    'description': '2019-01-07 - 2019-01-13'
                }
            ]
        },
        {
            'name': sprint_name,
            'cards': []
        },
        {
            'name': 'Sprint 1 - TO DO',
            'cards': [
                {
                    'name': 'card incomplete',
                    'movements': [],
                    'created_date': '2019-01-09T12:00:00'
                }
            ]
        }
    ]

    mock_trello_client(mocker, lists=lists)

    t = Trello()
    metrics = t.get_metrics()

    assert len(metrics) == 1
    assert metrics[0].num_completed == 0
    assert metrics[0].num_incomplete == 1


def test_trello_gets_no_incomplete_stories_not_moved_in_future(mocker):
    sprint_names = ['Done (week 1)', 'Done (week 2)']

    lists = [
        {
            'name': 'TM Q3 sprints',
            'cards': [
                {
                    'name': sprint_names[0],
                    'description': '2019-01-07 - 2019-01-13'
                },
                {
                    'name': sprint_names[1],
                    'description': '2019-01-14 - 2019-01-20'
                }

            ]
        },
        {
            'name': sprint_names[0],
            'cards': []
        },
        {
            'name': sprint_names[1],
            'cards': []
        },
        {
            'name': 'Sprint 2 - TO DO',
            'cards': [
                {
                    'name': 'card incomplete',
                    'movements': [],
                    'created_date': '2019-01-15T12:00:00'
                }
            ]
        }
    ]

    mock_trello_client(mocker, lists=lists)

    t = Trello()
    metrics = t.get_metrics()

    assert len(metrics) == 2
    assert metrics[0].num_completed == 0
    assert metrics[0].num_incomplete == 0
    assert metrics[1].num_completed == 0
    assert metrics[1].num_incomplete == 1


def test_trello_get_count_of_incomplete_and_complete_stories(mocker):
    sprint_name = 'Done (week 1)'

    lists = [
        {
            'name': 'TM Q3 sprints',
            'cards': [
                {
                    'name': sprint_name,
                    'description': '2019-01-07 - 2019-01-13'
                }
            ]
        },
        {
            'name': sprint_name,
            'cards': [
                {
                    'name': 'card done',
                    'movements': [
                        {
                            'datetime': '2019-01-07T12:00:00',
                            'source': 'Backlog',
                            'destination': 'Sprint 1 - TO DO'
                        },
                        {
                            'datetime': '2019-01-07T12:00:00',
                            'source': 'Sprint 1 - TO DO',
                            'destination': 'In Progress'
                        },
                        {
                            'datetime': '2019-01-08T12:00:00',
                            'source': 'In Progress',
                            'destination': 'Blocked'
                        },
                        {
                            'datetime': '2019-01-08T12:00:00',
                            'source': 'Blocked',
                            'destination': 'Sign off'
                        },
                        {
                            'datetime': '2019-01-08T13:00:00',
                            'source': 'Sign off',
                            'destination': 'Done (week 1)'
                        }
                    ]
                }
            ]
        },
        {
            'name': 'In Progress',
            'cards': [
                {
                    'name': 'card incomplete',
                    'movements': [
                        {
                            'datetime': '2019-01-07T12:00:00',
                            'source': 'Backlog',
                            'destination': 'Sprint 1 - TO DO'
                        },
                        {
                            'datetime': '2019-01-07T12:00:00',
                            'source': 'Sprint 1 - TO DO',
                            'destination': 'In Progress'
                        },
                    ]
                }
            ]
        }
    ]

    mock_trello_client(mocker, lists=lists)

    t = Trello()
    metrics = t.get_metrics()

    assert len(metrics) == 1
    assert metrics[0].num_completed == 1
    assert metrics[0].num_incomplete == 1


def test_trello_get_incomplete_story_count_over_2_sprints(mocker):
    sprint_names = [
        'Done (week 1)', 'Done (week 2)'
    ]

    lists = [
        {
            'name': 'TM Q3 sprints',
            'cards': [
                {
                    'name': sprint_names[0],
                    'description': '2019-01-07 - 2019-01-13'
                },
                {
                    'name': sprint_names[1],
                    'description': '2019-01-14 - 2019-01-20'
                }
            ]
        },
        {
            'name': sprint_names[0],
            'cards': []
        },
        {
            'name': sprint_names[1],
            'cards': []
        },
        {
            'name': 'In Progress',
            'cards': [
                {
                    'name': 'card incomplete',
                    'movements': [
                        {
                            'datetime': '2019-01-07T12:00:00',
                            'source': 'Backlog',
                            'destination': 'Sprint 1 - TO DO'
                        },
                        {
                            'datetime': '2019-01-07T12:00:00',
                            'source': 'Sprint 1 - TO DO',
                            'destination': 'In Progress'
                        },
                    ]
                }
            ]
        }
    ]

    mock_trello_client(mocker, lists=lists)

    t = Trello()
    metrics = t.get_metrics()

    assert len(metrics) == 2
    assert metrics[0].num_completed == 0
    assert metrics[0].num_incomplete == 1
    assert metrics[1].num_completed == 0
    assert metrics[1].num_incomplete == 1


def test_trello_get_incomplete_story_count_for_first_sprint(mocker):
    sprint_names = [
        'Done (week 1)', 'Done (week 2)'
    ]

    lists = [
        {
            'name': 'TM Q3 sprints',
            'cards': [
                {
                    'name': sprint_names[0],
                    'description': '2019-01-07 - 2019-01-13'
                },
                {
                    'name': sprint_names[1],
                    'description': '2019-01-14 - 2019-01-20'
                }
            ]
        },
        {
            'name': sprint_names[0],
            'cards': []
        },
        {
            'name': sprint_names[1],
            'cards': [
                {
                    'name': 'card incomplete in sprint 1',
                    'movements': [
                        {
                            'datetime': '2019-01-07T12:00:00',
                            'source': 'Backlog',
                            'destination': 'Sprint 1 - TO DO'
                        },
                        {
                            'datetime': '2019-01-07T12:00:00',
                            'source': 'Sprint 1 - TO DO',
                            'destination': 'In Progress'
                        },
                        {
                            'datetime': '2019-01-08T12:00:00',
                            'source': 'In Progress',
                            'destination': 'Blocked'
                        },
                        {
                            'datetime': '2019-01-10T12:00:00',
                            'source': 'Blocked',
                            'destination': 'In Progress'
                        },
                        {
                            'datetime': '2019-01-15T12:00:00',
                            'source': 'In Progress',
                            'destination': 'Sign off'
                        },
                        {
                            'datetime': '2019-01-15T12:00:00',
                            'source': 'Sign off',
                            'destination': sprint_names[1]
                        },
                    ]
                }
            ]
        },
    ]

    mock_trello_client(mocker, lists=lists)

    t = Trello()
    metrics = t.get_metrics()

    assert len(metrics) == 2
    assert metrics[0].num_completed == 0
    assert metrics[0].num_incomplete == 1
    assert metrics[1].num_completed == 1
    assert metrics[1].num_incomplete == 0


def test_trello_ignores_get_incomplete_story_count_out_of_sprint_dates(mocker):
    sprint_names = [
        'Done (week 1)', 'Done (week 2)', 'Done (week 3)'
    ]

    lists = [
        {
            'name': 'TM Q3 sprints',
            'cards': [
                {
                    'name': sprint_names[0],
                    'description': '2018-12-05 - 2018-12-11'
                },
                {
                    'name': sprint_names[1],
                    'description': '2018-12-12 - 2018-12-18'
                },
                {
                    'name': sprint_names[2],
                    'description': '2018-12-19 - 2018-12-25'
                },
            ]
        },
        {
            'name': 'In Progress',
            'cards': [
                {
                    'name': 'card in progress',
                    'movements': [
                        {
                            'datetime': '2018-12-12T11:00:00',
                            'source': 'Backlog',
                            'destination': 'Sprint 2 - TO DO'
                        },
                        {
                            'datetime': '2018-12-14T12:00:00',
                            'source': 'Sprint 2 - TO DO',
                            'destination': 'In Progress'
                        },
                    ]
                }
            ]
        },
        {
            'name': sprint_names[0],
            'cards': [
                {
                    'name': 'card complete in sprint 1',
                    'movements': [
                        {
                            'datetime': '2018-12-05T11:00:00',
                            'source': 'Backlog',
                            'destination': 'Sprint 1 - TO DO'
                        },
                        {
                            'datetime': '2018-12-05T12:00:00',
                            'source': 'Sprint 1 - TO DO',
                            'destination': 'In Progress'
                        },
                        {
                            'datetime': '2018-12-07T12:00:00',
                            'source': 'In Progress',
                            'destination': 'Sign off'
                        },
                        {
                            'datetime': '2018-12-08T12:00:00',
                            'source': 'Sign off',
                            'destination': sprint_names[0]
                        },
                    ]
                },
            ]
        },
        {
            'name': sprint_names[1],
            'cards': [
                {
                    'name': 'card complete in sprint 2',
                    'movements': [
                        {
                            'datetime': '2018-12-12T11:00:00',
                            'source': 'Backlog',
                            'destination': 'Sprint 2 - TO DO'
                        },
                        {
                            'datetime': '2018-12-12T12:00:00',
                            'source': 'Sprint 2 - TO DO',
                            'destination': 'In Progress'
                        },
                        {
                            'datetime': '2018-12-14T12:00:00',
                            'source': 'In Progress',
                            'destination': 'Sign off'
                        },
                        {
                            'datetime': '2018-12-15T12:00:00',
                            'source': 'Sign off',
                            'destination': sprint_names[1]
                        },

                    ]
                },
            ]
        },
        {
            'name': sprint_names[2],
            'cards': [
                {
                    'name': 'card complete in sprint 3',
                    'movements': [
                        {
                            'datetime': '2018-12-19T11:00:00',
                            'source': 'Backlog',
                            'destination': 'Sprint 3 - TO DO'
                        },
                        {
                            'datetime': '2018-12-19T12:00:00',
                            'source': 'Sprint 3 - TO DO',
                            'destination': 'In Progress'
                        },
                        {
                            'datetime': '2018-12-21T12:00:00',
                            'source': 'In Progress',
                            'destination': 'Sign off'
                        },
                        {
                            'datetime': '2018-12-22T12:00:00',
                            'source': 'Sign off',
                            'destination': sprint_names[2]
                        },
                    ]
                }
            ]
        },
    ]

    mock_trello_client(mocker, lists=lists)

    t = Trello()
    metrics = t.get_metrics()

    assert len(metrics) == 3
    assert metrics[0].num_completed == 1
    assert metrics[0].num_incomplete == 0
    assert metrics[1].num_completed == 1
    assert metrics[1].num_incomplete == 1
    assert metrics[2].num_completed == 1
    assert metrics[2].num_incomplete == 1


def test_trello_ignores_get_incomplete_story_count_out_of_sprint_dates_in_blocked(mocker):
    sprint_names = [
        'Done (week 1)', 'Done (week 2)'
    ]

    lists = [
        {
            'name': 'TM Q3 sprints',
            'cards': [
                {
                    'name': sprint_names[0],
                    'description': '2018-12-05 - 2018-12-11'
                },
                {
                    'name': sprint_names[1],
                    'description': '2018-12-12 - 2018-12-18'
                },
            ]
        },
        {
            'name': 'Blocked',
            'cards': [
                {
                    'name': 'card in blocked sprint 2',
                    'movements': [
                        {
                            'datetime': '2018-12-12T11:00:00',
                            'source': 'Backlog',
                            'destination': 'In Progress'
                        },
                        {
                            'datetime': '2018-12-14T12:00:00',
                            'source': 'In Progress',
                            'destination': 'Blocked'
                        },
                    ]
                }
            ]
        },
        {
            'name': sprint_names[0],
            'cards': []
        },
        {
            'name': sprint_names[1],
            'cards': []
        },
    ]

    mock_trello_client(mocker, lists=lists)

    t = Trello()
    metrics = t.get_metrics()

    assert len(metrics) == 2
    assert metrics[0].num_completed == 0
    assert metrics[0].num_incomplete == 0
    assert metrics[1].num_completed == 0
    assert metrics[1].num_incomplete == 1


def test_trello_get_incomplete_story_count_over_3_sprints(mocker):
    sprint_names = [
        'Done (week 1)', 'Done (week 2)', 'Done (week 3)'
    ]

    lists = [
        {
            'name': 'TM Q3 sprints',
            'cards': [
                {
                    'name': sprint_names[0],
                    'description': '2019-01-02 - 2019-01-08'
                },
                {
                    'name': sprint_names[1],
                    'description': '2019-01-09 - 2019-01-15'
                },
                {
                    'name': sprint_names[2],
                    'description': '2019-01-16 - 2019-01-22'
                },
            ]
        },
        {
            'name': sprint_names[0],
            'cards': [],
            'created_date': '2019-01-04T12:00:00'
        },
        {
            'name': sprint_names[1],
            'cards': []
        },
        {
            'name': sprint_names[2],
            'cards': [
                {
                    'name': 'card incomplete in sprint 1',
                    'movements': [
                        {
                            'datetime': '2019-01-15T12:00:00',
                            'source': 'Backlog',
                            'destination': 'Sprint 1 - TO DO'
                        },
                        {
                            'datetime': '2019-01-16T12:00:00',
                            'source': 'Sprint 1 - TO DO',
                            'destination': 'In Progress'
                        },
                        {
                            'datetime': '2019-01-17T12:00:00',
                            'source': 'In Progress',
                            'destination': 'Sign off'
                        },
                        {
                            'datetime': '2019-01-18T12:00:00',
                            'source': 'Sign off',
                            'destination': sprint_names[1]
                        },
                    ]
                }
            ]
        },
    ]

    mock_trello_client(mocker, lists=lists)

    t = Trello()
    metrics = t.get_metrics()

    assert len(metrics) == 3
    assert metrics[0].num_completed == 0
    assert metrics[0].num_incomplete == 0
    assert metrics[1].num_completed == 0
    assert metrics[1].num_incomplete == 1
    assert metrics[2].num_completed == 1
    assert metrics[2].num_incomplete == 0
