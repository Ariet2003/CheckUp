from aiogram.fsm.state import StatesGroup, State

# Registration
class AddAdmin(StatesGroup):
    full_name = State()
    role = State()
    login = State()
