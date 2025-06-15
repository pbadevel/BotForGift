from aiogram.fsm.state import StatesGroup, State

class EditEventState(StatesGroup):
    event_id = State()
    inp = State()
    photo = State()


class AddChannel(StatesGroup):
    
    channel_id = State()



class FindEvent(StatesGroup):
    event_name = State()


class SetWinners(StatesGroup):
    winners = State()

class AddEvent(StatesGroup):

    name = State()
    description = State()
    channel_event_ids=State()
    is_refferal = State()
    tickets_for_ref_count = State()
    win_count = State()
    end_date = State()


