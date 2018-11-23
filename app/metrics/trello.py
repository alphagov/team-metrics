import os
from trello import TrelloClient


class Trello:

    def __init__(self):
        self.pat = os.environ['TM_TRELLO_PAT']
        self.token = os.environ['TM_TRELLO_TOKEN']
        self.org_id = os.environ['TM_TRELLO_ORG_ID']
        self.board_id = os.environ['TM_TRELLO_BOARD_ID']

        self.trello = TrelloClient(
            api_key=self.pat,
            token=self.token,
        )

    def get_metrics(self):
        board = self.trello.get_board(self.board_id)
        print(board.name)
        lists = [l for l in board.list_lists() if l.name in ['Doing', 'Blocked', 'Done']]
        cards_in_done = 0
        for list_ in lists:
            print("  {}".format(list_.name))
            for card in list_.list_cards():
                print("    {}".format(card.name))

                def extract_datetime(json):
                    return json.get('datetime')

                movements = sorted(card.list_movements(), key=lambda d: d['datetime'])
                for movement in movements:
                    print("      {}: {} - {} ".format(movement['datetime'], movement['source']['name'], movement['destination']['name']))

                if list_.name == "Done":
                    cards_in_done = len(list_.list_cards())

        print('Cards in Done: {}'.format(cards_in_done))
