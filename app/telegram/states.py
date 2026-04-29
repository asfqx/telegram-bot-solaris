from aiogram.fsm.state import State, StatesGroup


class RequestLeadState(StatesGroup):
    
    waiting_for_name = State()
    waiting_for_people_count = State()
    waiting_for_age = State()
    waiting_for_comment = State()
    waiting_for_booking_datetime = State()
    waiting_for_phone = State()
    waiting_for_event_details = State()
    waiting_for_confirmation = State()
