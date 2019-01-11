import os
import re
from datetime import timedelta
from trello import TrelloClient

from app.metrics import Metrics
from app.source import Base, get_time_diff, get_process_cycle_efficiency


# As Trello is completely free form, the app will need to make some assumptions
# on how a teams manages their boards, cards and lists
#
# The following rules are based on RE Observe trello board:
#
# How do we get access to other lists? we have to unarchive them,
# or find them in the archived list and check if the dates correspond to a quarter time range
# presume a quarter starts from October - End December/First week of Jan
#
# Introduce a function to calculate the quarters date range including firebreak?

def get_quarter_start(year, quarter):
    # calculate from year the quarter part
    # but for now just return back 2018 Q3
    return '2018-10-08'

#
# Different quarters are split into different boards, eg Team name - Q1
#
# Actually we use the same board but archive the Done lists, these are eventually deleted
# Boards are renamed for teh quarter
#
# Week dates will be imported as a key for the weeks works from list
#  - TM week dates Q3

# TO DO sprint get renamed at the start of each sprint
# - check if we can get history of the list renaming,
#  then get the datetime of when the list was renamed or get it from the week dates list

# Done cards for sprints are in different lists, eg Done Sprint 1
# Need to keep track of an authority list for the different list names
# - Sprint n - TO DO, Doing, Blocked, Done Sprint n
#   - should be possible to make this configurable if needed
# incomplete stories are in TO_DO, IN_PROGRESS or BLOCKED

# Cycle time is calculated as card in Doing to Sign off

# Blocked look at whether sent back to In Progress or Sign off

TO_DO = r'Sprint \d - TO DO|To do this iteration .*'
DOING = r'Doing|In Progress'
BLOCKED = r'Blocked'
SIGN_OFF = r'Sign off'
DONE = r'^Done\s.+'
SPRINTS = 'TM Q3 sprints'
IGNORE_CARDS = 'SPRINT GOALS #DONOTMOVE'

DOING_TRELLO_LIST = r"{}|{}".format(TO_DO, DOING)
INCOMPLETED_TRELLO_LIST = r"{}|{}|{}".format(TO_DO, DOING, BLOCKED)
COMPLETED_TRELLO_LIST = r"{}|{}".format(SIGN_OFF, DONE)


class Trello(Base):

    def __init__(self, board_id=None, sprint_id=None):
        self.pat = os.environ['TM_TRELLO_PAT']
        self.token = os.environ['TM_TRELLO_TOKEN']
        self.org_id = os.environ['TM_TRELLO_ORG_ID']
        self.board_id = board_id
        self.sprint_id = sprint_id

        self.trello = TrelloClient(
            api_key=self.pat,
            token=self.token,
        )

    def get_in_progress_time(self, card):
        movements = sorted(card.list_movements(), key=lambda d: d['datetime'])

        in_progress_start = []
        in_progress_end = []

        if re.match(DOING, movements[0]['source']['name']):
            in_progress_start.append(card.created_date) if card.created_date else None

        for movement in movements:
            if re.match(DOING, movement['destination']['name']):
                in_progress_start.append(movement['datetime'])
            if re.match(DOING, movement['source']['name']):
                in_progress_end.append(movement['datetime'])

        if in_progress_start and in_progress_end:
            in_progress_time = timedelta()
            for i, start in enumerate(in_progress_start):
                end = in_progress_end[i]
                in_progress_time += get_time_diff(start, end)

            return in_progress_time

    def get_blocked_time(self, card):
        movements = sorted(card.list_movements(), key=lambda d: d['datetime'])

        blocked_start = []
        blocked_end = []

        for movement in movements:
            if re.match(BLOCKED, movement['destination']['name']):
                blocked_start.append(movement['datetime'])
            if re.match(BLOCKED, movement['source']['name']):
                blocked_end.append(movement['datetime'])

        if blocked_start and blocked_end:
            blocked_time = timedelta()
            for i, start in enumerate(blocked_start):
                end = blocked_end[i]
                blocked_time += get_time_diff(start, end)

            return blocked_time
        return timedelta()

    def get_cards_incomplete(self, lists, start_date, end_date):
        # incomplete stories are in TO_DO, IN_PROGRESS or BLOCKED after the sprint end date
        # to calculate incomplete cards within a sprint we need to go through each card
        # when the card gets moved to Done, we will probably have to revisit all the cards to
        # see how long they spent in each list during the sprint

        # end of sprint time should be just before midnight
        end_date = '{}T23:59:59'.format(end_date)

        incomplete_count = 0
        lists = [l for l in lists if re.match("{}|{}".format(
            INCOMPLETED_TRELLO_LIST, COMPLETED_TRELLO_LIST), l.name) and not l.closed]
        for _list in lists:
            print('*** processing cards in ', _list.name)
            for card in _list.list_cards():
                if card.name == IGNORE_CARDS:
                    continue

                outside_or_completed = False

                movements = sorted(card.list_movements(), key=lambda d: d['datetime'])

                if not movements and (str(card.created_date) < start_date or str(card.created_date) > end_date):
                    outside_or_completed = True
                else:
                    doing_start = None

                    # if a card is created within a list, the first list is the source
                    if movements and re.match(DOING_TRELLO_LIST, movements[0]['source']['name']):
                        doing_start = str(card.created_date) if card.created_date else None
                    else:
                        # find date it's first moved to DOING
                        for movement in movements:
                            if not doing_start and \
                                (re.match(INCOMPLETED_TRELLO_LIST, movement['destination']['name']) or
                                re.match(COMPLETED_TRELLO_LIST, movement['destination']['name'])
                            ):
                                doing_start = str(movement['datetime'])
                                break

                    if doing_start and doing_start > end_date:
                        outside_or_completed = True

                    if not outside_or_completed:
                        for movement in movements:
                            if str(movement['datetime']) > end_date:
                                # if the movement is after the sprint and the card is matching DOING, then can ignore
                                # if the movement is after the sprint but not DOING then it's probably moved to next sprint
                                if re.match(DOING_TRELLO_LIST, movement['destination']['name']):
                                    if doing_start < start_date:
                                        outside_or_completed = True
                                break

                            if (re.match(COMPLETED_TRELLO_LIST, movement['destination']['name'])):
                                outside_or_completed = True
                                break

                if not outside_or_completed:
                    print('incomplete', card.name)
                    incomplete_count += 1

        return incomplete_count

    def get_metrics(self, last_num_weeks=None):
        board = self.trello.get_board(self.board_id)
        print(board.name)

        sprints = [l for l in board.list_lists() if l.name == SPRINTS][0]
        sprints_cards = sorted(sprints.list_cards(), key=lambda d: d.description)

        done_lists = []

        open_lists = [l for l in board.list_lists() if not l.closed]

        for _list in open_lists:
            sprint_card = [w for w in sprints_cards if w.name == _list.name]
            if sprint_card:
                _list.start_date = sprint_card[0].description.split(' - ')[0]
                _list.end_date = sprint_card[0].description.split(' - ')[1]
                done_lists.append(_list)

        done_lists = sorted(done_lists, key=lambda d: d.start_date)

        cards_in_done = 0
        metrics = []

        for _list in done_lists:
            if self.sprint_id and _list.id != self.sprint_id:
                continue

            print("  {}".format(_list.name))

            cycle_time = timedelta(days=0)
            process_cycle_efficiency = 0

            for card in _list.list_cards():
                print("    {}".format(card.name))

                in_progress_time = self.get_in_progress_time(card)

                if not in_progress_time:
                    print('*** no progress on card', card.name)
                    continue

                blocked_time = self.get_blocked_time(card)

                cycle_time += in_progress_time + blocked_time

                process_cycle_efficiency += get_process_cycle_efficiency(
                                cycle_time, blocked_time)

            cards_in_done = len(_list.list_cards())

            num_incomplete = self.get_cards_incomplete(
                board.list_lists(), _list.start_date, _list.end_date)

            m = Metrics(
                self.board_id,
                _list.id,
                _list.start_date,
                _list.end_date,
                "trello",
                0 if not cycle_time else cycle_time / cards_in_done,
                (process_cycle_efficiency / cards_in_done) if cards_in_done else 0,
                cards_in_done,
                num_incomplete
            )
            metrics.append(m)

        print('Cards in Done: {}'.format(cards_in_done))
        return metrics
