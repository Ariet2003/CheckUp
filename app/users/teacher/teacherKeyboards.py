from typing import List

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database import requests as rq

teacher_account = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Отметить группу", callback_data="mark_group"),
     InlineKeyboardButton(text="📜 Расписание", callback_data="view_schedule")]
])


async def student_check_buttons(students: List[dict], selected_students: List[int]) -> InlineKeyboardMarkup:
    """
    Создает кнопки для списка студентов.

    :param students: Список студентов в формате {"student_id": int, "name": str}.
    :param selected_students: Список student_id выбранных студентов.
    :return: InlineKeyboardMarkup с кнопками.
    """
    keyboard = InlineKeyboardBuilder()

    for student in students:
        text = student['name']
        if student['student_id'] in selected_students:
            text += " ✅"
        keyboard.add(
            InlineKeyboardButton(
                text=text,
                callback_data=f"student_check_{student['student_id']}"
            )
        )
    keyboard.add(InlineKeyboardButton(text="✈️ Готово", callback_data="finish_selection"))
    keyboard.add(InlineKeyboardButton(text="⬅️ Личный кабинет", callback_data="go_home_teacher"))

    return keyboard.adjust(1).as_markup()

go_to_teacher = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⬅️ Личный кабинет", callback_data="go_home_teacher")]
])