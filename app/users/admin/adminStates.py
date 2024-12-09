from aiogram.fsm.state import StatesGroup, State

class AddAdmin(StatesGroup):
    full_name = State()
    role = State()
    login = State()

class DeleteAdmin(StatesGroup):
    login = State()

class AddTeacher(StatesGroup):
    full_name = State()
    login = State()

class DeleteTeacher(StatesGroup):
    login = State()