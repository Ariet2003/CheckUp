import re
from datetime import datetime

from aiogram.client.session import aiohttp
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from app.database.models import UserRole
from app.utils import router, sent_message_add_screen_ids
from aiogram import F, Router
from aiogram.types import FSInputFile
from app.users.teacher import teacherKeyboards as kb
from app.users.admin import adminStates as st
from app import utils
from app.database import requests as rq
from aiogram.fsm.context import FSMContext
import os
from app.utils import sent_message_add_screen_ids, router


# Function to delete previous messages
async def delete_previous_messages(message: Message, telegram_id: str):
    # Проверяем, есть ли записи для этого пользователя
    if telegram_id not in sent_message_add_screen_ids:
        sent_message_add_screen_ids[telegram_id] = {'bot_messages': [], 'user_messages': []}

    user_data = sent_message_add_screen_ids[telegram_id]

    # Удаляем все сообщения пользователя, кроме "/start"
    for msg_id in user_data['user_messages']:
        try:
            if msg_id != message.message_id or message.text != "/start":
                await message.bot.delete_message(chat_id=telegram_id, message_id=msg_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение {msg_id}: {e}")
    user_data['user_messages'].clear()

    # Удаляем все сообщения бота
    for msg_id in user_data['bot_messages']:
        try:
            if msg_id != message.message_id:
                await message.bot.delete_message(chat_id=telegram_id, message_id=msg_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение {msg_id}: {e}")
    user_data['bot_messages'].clear()


async def teacher_account(message: Message, state: FSMContext):
    tuid = message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    # Добавляем сообщение пользователя
    user_data['user_messages'].append(message.message_id)
    # Удаляем предыдущие сообщения
    await delete_previous_messages(message, tuid)
    name = await rq.get_name(str(tuid))
    sent_message = await message.answer_photo(
        photo=utils.teacherAccountPicture,
        caption=f'Привет, {name}',
        reply_markup=kb.teacher_account
    )
    # Добавляем сообщение бота
    user_data['bot_messages'].append(sent_message.message_id)



@router.callback_query(F.data.in_('go_home_teacher'))
async def go_home_teacher(callback: CallbackQuery, state: FSMContext):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['bot_messages'].append(callback.message.message_id)
    await teacher_account(callback.message, state)

@router.callback_query(F.data == 'mark_group')
async def mark_group(callback: CallbackQuery, state: FSMContext):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(callback.message.message_id)
    await delete_previous_messages(callback.message, tuid)

    # Получаем список студентов для текущего занятия
    list_student_id = await rq.get_students_for_current_lesson(telegram_id=tuid)

    # Преобразуем список student_id в список словарей с именами
    students = await rq.get_student_names_by_ids(list_student_id)

    # Сохраняем список студентов в state
    await state.update_data(students=students, selected_students=[])

    sent_message = await callback.message.answer_photo(
        photo=utils.teacherAccountPicture,
        caption="Выберите студента:",
        reply_markup=await kb.student_check_buttons(students, selected_students=[])
    )
    # Добавляем сообщение бота
    user_data['bot_messages'].append(sent_message.message_id)

@router.callback_query(F.data.startswith('student_check_'))
async def select_student(callback: CallbackQuery, state: FSMContext):
    student_id = int(callback.data.split("_")[-1])

    # Получаем текущие данные из state
    data = await state.get_data()
    selected_students = data.get("selected_students", [])

    # Добавляем или удаляем student_id из выбранных
    if student_id in selected_students:
        selected_students.remove(student_id)
    else:
        selected_students.append(student_id)

    # Сохраняем обновленные данные
    await state.update_data(selected_students=selected_students)

    # Перегенерируем кнопки
    students = data.get("students", [])
    await callback.message.edit_reply_markup(
        reply_markup=await kb.student_check_buttons(students, selected_students)
    )

@router.callback_query(F.data == "finish_selection")
async def finish_selection(callback: CallbackQuery, state: FSMContext):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(callback.message.message_id)
    await delete_previous_messages(callback.message, tuid)

    # Получаем выбранных студентов из state
    data = await state.get_data()
    selected_students = data.get("selected_students", [])

    data = await state.get_data()
    students = data.get("students")

    # Извлекаем только student_id из списка словарей students
    all_student_ids = {student["student_id"] for student in students}

    # Преобразуем selected_students в множество
    selected_student_ids = set(selected_students)

    # Находим невыбранных студентов
    unselected_student_ids = all_student_ids - selected_student_ids

    # Если нужен список словарей для невыбранных студентов
    unselected_students = [
        student for student in students if student["student_id"] in unselected_student_ids
    ]

    unselected_students = [student['student_id'] for student in unselected_students]

    result = await rq.record_attendance(
        checked_student_id=selected_students,
        unchecked_student_id=unselected_students,
        telegram_id=callback.message.chat.id
    )

    if result:
        sent_message = await callback.message.answer_photo(
            photo=utils.teacherAccountPicture,
            caption="Посещаемость успешно записана!",
            reply_markup=kb.go_to_teacher
        )
        # Добавляем сообщение бота
        user_data['bot_messages'].append(sent_message.message_id)

        await state.clear()

    else:
        sent_message = await callback.message.answer_photo(
            photo=utils.teacherAccountPicture,
            caption="Ошибка при записи посещаемости. Может быть посещаемость для этого занятия уже была записана.",
            reply_markup=kb.go_to_teacher
        )
        # Добавляем сообщение бота
        user_data['bot_messages'].append(sent_message.message_id)

        await state.clear()


@router.callback_query(F.data == 'view_schedule')
async def view_schedule(callback: CallbackQuery, state: FSMContext):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(callback.message.message_id)
    await delete_previous_messages(callback.message, tuid)

    schedule = await rq.get_simple_teacher_schedule(str(tuid))

    sent_message = await callback.message.answer(
        text=schedule,
        reply_markup=kb.go_to_teacher,
        ParseMode=ParseMode.MARKDOWN
    )

    # Добавляем сообщение бота
    user_data['bot_messages'].append(sent_message.message_id)
