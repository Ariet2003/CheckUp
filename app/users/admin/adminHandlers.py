import re
from datetime import datetime

from aiogram.client.session import aiohttp
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from app.database.models import UserRole
from app.users.teacher.teacherHandlers import teacher_account
from app.utils import router, sent_message_add_screen_ids
from aiogram import F, Router
from aiogram.types import FSInputFile
from app.users.admin import adminKeyboards as kb
from app.users.admin import adminStates as st
from app import utils
from app.database import requests as rq
from aiogram.fsm.context import FSMContext
import os
from app.utils import sent_message_add_screen_ids, router


# Хендлер для обработки команды "/photo"
@router.message(Command("photo"))
async def request_photo_handler(message: Message):
    await message.answer("Пожалуйста, отправьте фото, чтобы я мог получить его ID.")


# Хендлер для обработки фото от пользователя
@router.message(F.photo)
async def photo_handler(message: Message):
    # Берем фотографию в самом большом разрешении и получаем ее ID
    photo_id = message.photo[-1].file_id
    await message.answer(f"ID вашей картинки: {photo_id}")


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

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    tuid = message.chat.id
    # Инициализируем словарь для нового пользователя, если его еще нет
    if tuid not in sent_message_add_screen_ids:
        sent_message_add_screen_ids[tuid] = {'bot_messages': [], 'user_messages': []}
    user_data = sent_message_add_screen_ids[tuid]
    is_admin = await rq.check_admin(telegram_id=str(tuid))
    if is_admin:
        await admin_account(message, state)
    else:
        await teacher_account(message, state)


async def admin_account(message: Message, state: FSMContext):
    tuid = message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    # Добавляем сообщение пользователя
    user_data['user_messages'].append(message.message_id)
    # Удаляем предыдущие сообщения
    await delete_previous_messages(message, tuid)
    name = await rq.get_name(str(tuid))
    sent_message = await message.answer_photo(
        photo=utils.adminAccountPicture,
        caption=f'Привет, {name}',
        reply_markup=kb.admin_account
    )
    # Добавляем сообщение бота
    user_data['bot_messages'].append(sent_message.message_id)

@router.callback_query(F.data == 'view_user')
async def view_user_handler(callback: CallbackQuery):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(callback.message.message_id)
    await delete_previous_messages(callback.message, tuid)

    sent_message = await callback.message.answer_photo(
        photo=utils.adminViewUsersPicture,
        caption="Выберите действие",
        reply_markup=kb.view_users
    )
    user_data['bot_messages'].append(sent_message.message_id)

@router.callback_query(F.data.in_('go_home_admin'))
async def go_home_admin(callback: CallbackQuery, state: FSMContext):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['bot_messages'].append(callback.message.message_id)
    await admin_account(callback.message, state)

@router.callback_query(F.data == 'add_admin')
async def add_admin(callback: CallbackQuery, state: FSMContext):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(callback.message.message_id)
    await delete_previous_messages(callback.message, tuid)

    is_super_admin = await rq.check_super_admin(telegram_id=tuid)
    if is_super_admin:
        sent_message = await callback.message.answer_photo(
            photo=utils.adminViewUsersPicture,
            caption="Напишите ФИО администратора"
        )
        user_data['bot_messages'].append(sent_message.message_id)
    else:
        sent_message = await callback.message.answer_photo(
            photo=utils.adminViewUsersPicture,
            caption="Вы не можете совершить это действие.",
            reply_markup=kb.go_to_admin
        )
        user_data['bot_messages'].append(sent_message.message_id)
    await state.set_state(st.AddAdmin.full_name)

@router.message(st.AddAdmin.full_name)
async def add_admin_full_name(message: Message, state: FSMContext):
    tuid = message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(message.message_id)
    await delete_previous_messages(message, tuid)

    admin_full_name = message.text
    await state.update_data(admin_full_name=admin_full_name)

    sent_message = await message.answer_photo(
        photo=utils.adminViewUsersPicture,
        caption="Напишите 1, если хотите назначить его супер администратором, 0 — если администратором."
    )
    user_data['bot_messages'].append(sent_message.message_id)
    await state.set_state(st.AddAdmin.role)

@router.message(st.AddAdmin.role)
async def add_admin_role(message: Message, state: FSMContext):
    tuid = message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(message.message_id)
    await delete_previous_messages(message, tuid)

    admin_role = message.text
    await state.update_data(admin_role=admin_role)

    sent_message = await message.answer_photo(
        photo=utils.adminViewUsersPicture,
        caption="Напишите TELEGRAM ID администратора"
    )
    user_data['bot_messages'].append(sent_message.message_id)
    await state.set_state(st.AddAdmin.login)

@router.message(st.AddAdmin.login)
async def add_admin_login(message: Message, state: FSMContext):
    tuid = message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(message.message_id)
    await delete_previous_messages(message, tuid)

    admin_login = message.text

    data = await state.get_data()
    admin_full_name = data.get("admin_full_name")
    admin_role = data.get("admin_role")
    if admin_role == "1":
        admin_role = "SUPERADMIN"
    else:
        admin_role = "ADMIN"

    is_added = await rq.add_user(full_name=admin_full_name, role=admin_role, login=admin_login)
    if is_added:
        sent_message = await message.answer_photo(
            photo=utils.adminViewUsersPicture,
            caption="Пользователь успешно добавлен",
            reply_markup=kb.go_to_admin
        )
        user_data['bot_messages'].append(sent_message.message_id)
    else:
        sent_message = await message.answer_photo(
            photo=utils.adminViewUsersPicture,
            caption="Произошла ошибка или пользователь уже существует, попробуйте добавить еще раз.",
            reply_markup=kb.go_to_admin
        )
        user_data['bot_messages'].append(sent_message.message_id)


    await state.clear()

@router.callback_query(F.data == 'delete_admin')
async def add_admin(callback: CallbackQuery, state: FSMContext):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(callback.message.message_id)
    await delete_previous_messages(callback.message, tuid)

    is_super_admin = await rq.check_super_admin(telegram_id=tuid)
    if is_super_admin:
        sent_message = await callback.message.answer_photo(
            photo=utils.adminViewUsersPicture,
            caption="Напишите TELEGRAM ID администратора"
        )
        user_data['bot_messages'].append(sent_message.message_id)
        await state.set_state(st.DeleteAdmin.login)
    else:
        sent_message = await callback.message.answer_photo(
            photo=utils.adminViewUsersPicture,
            caption="Вы не можете совершить это действие.",
            reply_markup=kb.go_to_admin
        )
        user_data['bot_messages'].append(sent_message.message_id)


@router.message(st.DeleteAdmin.login)
async def delete_admin(message: Message, state: FSMContext):
    tuid = message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(message.message_id)
    await delete_previous_messages(message, tuid)
    telegram_id_admin = message.text

    await state.update_data(telegram_id_admin=telegram_id_admin)
    sent_message = await message.answer_photo(
        photo=utils.adminViewUsersPicture,
        caption=f"Вы действительно хотите удалить админа с Telegram ID = {telegram_id_admin}?",
        reply_markup=kb.deleting_confirmation(telegram_id=str(telegram_id_admin))
    )
    user_data['bot_messages'].append(sent_message.message_id)

@router.callback_query(lambda c: c.data and c.data.startswith("delete_admin_"))
async def delete_admin_finish(callback: CallbackQuery, state: FSMContext):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(callback.message.message_id)
    await delete_previous_messages(callback.message, tuid)

    admin_telegram_id = str(callback.data.split("_")[2])

    is_deleted = await rq.delete_admin(telegram_id=admin_telegram_id)

    if is_deleted:
        sent_message = await callback.message.answer_photo(
            photo=utils.adminViewUsersPicture,
            caption="Администратор успешно удален.",
            reply_markup=kb.go_to_admin
        )
        user_data['bot_messages'].append(sent_message.message_id)
        await state.clear()

    else:
        sent_message = await callback.message.answer_photo(
            photo=utils.adminViewUsersPicture,
            caption="Администратор не удалён, произошла ошибка.",
            reply_markup=kb.go_to_admin
        )
        user_data['bot_messages'].append(sent_message.message_id)
        await state.clear()

@router.callback_query(F.data == 'add_teacher')
async def add_teacher(callback: CallbackQuery, state: FSMContext):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(callback.message.message_id)
    await delete_previous_messages(callback.message, tuid)

    is_super_admin = await rq.check_super_admin(telegram_id=tuid)
    if is_super_admin:
        sent_message = await callback.message.answer_photo(
            photo=utils.adminViewUsersPicture,
            caption="Напишите ФИО преподавателя"
        )
        user_data['bot_messages'].append(sent_message.message_id)
    else:
        sent_message = await callback.message.answer_photo(
            photo=utils.adminViewUsersPicture,
            caption="Вы не можете совершить это действие.",
            reply_markup=kb.go_to_admin
        )
        user_data['bot_messages'].append(sent_message.message_id)
    await state.set_state(st.AddTeacher.full_name)

@router.message(st.AddTeacher.full_name)
async def add_teacher_full_name(message: Message, state: FSMContext):
    tuid = message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(message.message_id)
    await delete_previous_messages(message, tuid)

    teacher_full_name = message.text
    await state.update_data(teacher_full_name=teacher_full_name)

    sent_message = await message.answer_photo(
        photo=utils.adminViewUsersPicture,
        caption="Напишите TELEGRAM ID преподавателя"
    )
    user_data['bot_messages'].append(sent_message.message_id)
    await state.set_state(st.AddTeacher.login)

@router.message(st.AddTeacher.login)
async def add_teacher_login(message: Message, state: FSMContext):
    tuid = message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(message.message_id)
    await delete_previous_messages(message, tuid)

    teacher_login = message.text

    data = await state.get_data()
    teacher_full_name = data.get("teacher_full_name")
    teacher_role = "TEACHER"
    is_added = await rq.add_user(full_name=teacher_full_name, role=teacher_role, login=teacher_login)
    if is_added:
        sent_message = await message.answer_photo(
            photo=utils.adminViewUsersPicture,
            caption="Пользователь успешно добавлен",
            reply_markup=kb.go_to_admin
        )
        user_data['bot_messages'].append(sent_message.message_id)
    else:
        sent_message = await message.answer_photo(
            photo=utils.adminViewUsersPicture,
            caption="Произошла ошибка или пользователь уже существует, попробуйте добавить еще раз.",
            reply_markup=kb.go_to_admin
        )
        user_data['bot_messages'].append(sent_message.message_id)


    await state.clear()

@router.callback_query(F.data == 'delete_teacher')
async def delete_admin(callback: CallbackQuery, state: FSMContext):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(callback.message.message_id)
    await delete_previous_messages(callback.message, tuid)

    is_super_admin = await rq.check_super_admin(telegram_id=tuid)
    if is_super_admin:
        sent_message = await callback.message.answer_photo(
            photo=utils.adminViewUsersPicture,
            caption="Напишите TELEGRAM ID преподавателя"
        )
        user_data['bot_messages'].append(sent_message.message_id)
        await state.set_state(st.DeleteTeacher.login)
    else:
        sent_message = await callback.message.answer_photo(
            photo=utils.adminViewUsersPicture,
            caption="Вы не можете совершить это действие.",
            reply_markup=kb.go_to_admin
        )
        user_data['bot_messages'].append(sent_message.message_id)


@router.message(st.DeleteTeacher.login)
async def delete_teacher(message: Message, state: FSMContext):
    tuid = message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(message.message_id)
    await delete_previous_messages(message, tuid)
    telegram_id_teacher = message.text

    await state.update_data(telegram_id_teacher=telegram_id_teacher)
    sent_message = await message.answer_photo(
        photo=utils.adminViewUsersPicture,
        caption=f"Вы действительно хотите удалить преподавателя с Telegram ID = {telegram_id_teacher}?",
        reply_markup=kb.deleting_confirmation_teacher(telegram_id=str(telegram_id_teacher))
    )
    user_data['bot_messages'].append(sent_message.message_id)

@router.callback_query(lambda c: c.data and c.data.startswith("delete_teacher_"))
async def delete_teacher_finish(callback: CallbackQuery, state: FSMContext):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(callback.message.message_id)
    await delete_previous_messages(callback.message, tuid)

    teacher_telegram_id = str(callback.data.split("_")[2])

    is_deleted = await rq.delete_teacher(telegram_id=teacher_telegram_id)

    if is_deleted:
        sent_message = await callback.message.answer_photo(
            photo=utils.adminViewUsersPicture,
            caption="Преподаватель успешно удален.",
            reply_markup=kb.go_to_admin
        )
        user_data['bot_messages'].append(sent_message.message_id)
        await state.clear()

    else:
        sent_message = await callback.message.answer_photo(
            photo=utils.adminViewUsersPicture,
            caption="Преподаватель не удалён, произошла ошибка.",
            reply_markup=kb.go_to_admin
        )
        user_data['bot_messages'].append(sent_message.message_id)
        await state.clear()

@router.callback_query(F.data == 'list_teacher')
async def list_teacher(callback: CallbackQuery, state: FSMContext):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(callback.message.message_id)
    await delete_previous_messages(callback.message, tuid)

    sent_message = await callback.message.answer_photo(
        photo=utils.adminViewUsersPicture,
        caption="Вы можете экспортировать список преподавателей в формате Excel..",
        reply_markup=kb.export_teacher
    )
    user_data['bot_messages'].append(sent_message.message_id)

@router.callback_query(F.data == 'export_teacher')
async def export_teacher(callback: CallbackQuery, state: FSMContext):
    try:
        tuid = callback.message.chat.id
        user_data = sent_message_add_screen_ids[tuid]
        user_data['user_messages'].append(callback.message.message_id)
        await delete_previous_messages(callback.message, tuid)

        # Определяем путь к файлу в каталоге проекта
        filename = os.path.join(os.getcwd(), "teachers.xlsx")
        is_generate = await rq.export_users_to_excel_by_role(role=UserRole.TEACHER, filename=filename)

        if is_generate:
            # Отправляем файл пользователю
            if os.path.exists(filename):
                file = FSInputFile(filename)
                sent_message = await callback.message.answer_document(
                    document=file,
                    caption="Готово! Вот ваш файл.",
                    reply_markup=kb.go_to_admin
                )
                user_data['bot_messages'].append(sent_message.message_id)

                # Удаляем файл после отправки
                os.remove(filename)
            else:
                await callback.message.answer("Файл не найден после генерации.")
        else:
            sent_message = await callback.message.answer_photo(
                photo=utils.adminViewUsersPicture,
                caption="Ошибка при создании файла. Данные отсутствуют.",
                reply_markup=kb.go_to_admin
            )
            user_data['bot_messages'].append(sent_message.message_id)
    except Exception as e:
        print(f"Error in export_teacher: {e}")
        await callback.message.answer("Произошла ошибка. Попробуйте еще раз.")


@router.callback_query(F.data == 'list_admin')
async def list_admin(callback: CallbackQuery, state: FSMContext):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(callback.message.message_id)
    await delete_previous_messages(callback.message, tuid)

    sent_message = await callback.message.answer_photo(
        photo=utils.adminViewUsersPicture,
        caption="Вы можете экспортировать список администраторов в формате Excel..",
        reply_markup=kb.export_admin
    )
    user_data['bot_messages'].append(sent_message.message_id)

@router.callback_query(F.data == 'export_admin')
async def export_admin(callback: CallbackQuery, state: FSMContext):
    try:
        tuid = callback.message.chat.id
        user_data = sent_message_add_screen_ids[tuid]
        user_data['user_messages'].append(callback.message.message_id)
        await delete_previous_messages(callback.message, tuid)

        # Определяем путь к файлу в каталоге проекта
        filename = os.path.join(os.getcwd(), "admins.xlsx")
        is_generate = await rq.export_users_to_excel_by_role(role=UserRole.ADMIN, filename=filename)

        if is_generate:
            # Отправляем файл пользователю
            if os.path.exists(filename):
                file = FSInputFile(filename)
                sent_message = await callback.message.answer_document(
                    document=file,
                    caption="Готово! Вот ваш файл.",
                    reply_markup=kb.go_to_admin
                )
                user_data['bot_messages'].append(sent_message.message_id)

                # Удаляем файл после отправки
                os.remove(filename)
            else:
                await callback.message.answer("Файл не найден после генерации.")
        else:
            sent_message = await callback.message.answer_photo(
                photo=utils.adminViewUsersPicture,
                caption="Ошибка при создании файла. Данные отсутствуют.",
                reply_markup=kb.go_to_admin
            )
            user_data['bot_messages'].append(sent_message.message_id)
    except Exception as e:
        print(f"Error in export_teacher: {e}")
        await callback.message.answer("Произошла ошибка. Попробуйте еще раз.")

@router.callback_query(F.data == 'view_statistics')
async def view_statistics(callback: CallbackQuery):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(callback.message.message_id)
    await delete_previous_messages(callback.message, tuid)

    statistic = await rq.get_university_statistics()

    sent_message = await callback.message.answer(
        text=statistic,
        reply_markup=kb.go_to_admin,
        parse_mode=ParseMode.MARKDOWN
    )
    user_data['bot_messages'].append(sent_message.message_id)

@router.callback_query(F.data == 'admin_manage')
async def admin_manage(callback: CallbackQuery):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(callback.message.message_id)
    await delete_previous_messages(callback.message, tuid)

    sent_message = await callback.message.answer_photo(
        photo=utils.adminManagePicture,
        caption="Выберите действие",
        reply_markup=kb.manage_admin
    )

    user_data['bot_messages'].append(sent_message.message_id)

@router.callback_query(F.data == 'manage_faculty')
async def manage_faculty(callback: CallbackQuery):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(callback.message.message_id)
    await delete_previous_messages(callback.message, tuid)

    sent_message = await callback.message.answer_photo(
        photo=utils.adminManagePicture,
        caption="Вы можете экспортировать все данные о факультете в формате Excel."
                "\nМожете импортировать данные из файла Excel в БД",
        reply_markup=kb.manage_faculties
    )

    user_data['bot_messages'].append(sent_message.message_id)

@router.callback_query(F.data == 'export_faculty')
async def export_faculty(callback: CallbackQuery, state: FSMContext):
    try:
        tuid = callback.message.chat.id
        user_data = sent_message_add_screen_ids[tuid]
        user_data['user_messages'].append(callback.message.message_id)
        await delete_previous_messages(callback.message, tuid)

        # Определяем путь к файлу в каталоге проекта
        filename = os.path.join(os.getcwd(), "faculties.xlsx")
        is_generate = await rq.export_faculties_to_excel(filename=filename)

        if is_generate:
            # Отправляем файл пользователю
            if os.path.exists(filename):
                file = FSInputFile(filename)
                sent_message = await callback.message.answer_document(
                    document=file,
                    caption="Готово! Вот данные факультетов.",
                    reply_markup=kb.go_to_admin
                )
                user_data['bot_messages'].append(sent_message.message_id)

                # Удаляем файл после отправки
                os.remove(filename)
            else:
                await callback.message.answer("Файл не найден после генерации.",
                                              reply_markup=kb.go_to_admin)
        else:
            sent_message = await callback.message.answer(
                "Ошибка при создании файла. Данные отсутствуют.",
                reply_markup=kb.go_to_admin
            )
            user_data['bot_messages'].append(sent_message.message_id)
    except Exception as e:
        print(f"Error in export_faculty: {e}")
        await callback.message.answer("Произошла ошибка. Попробуйте еще раз.",
                                      reply_markup=kb.go_to_admin)

@router.callback_query(F.data == 'import_faculty')
async def import_faculties(callback: CallbackQuery, state: FSMContext):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(callback.message.message_id)
    await delete_previous_messages(callback.message, tuid)
    sent_message = await callback.message.answer(
        "Отправьте файл в формате Excel.",
    reply_markup=kb.go_to_admin
    )
    user_data['bot_messages'].append(sent_message.message_id)
    await state.set_state(st.ImportFaculties.sendFile)


@router.message(st.ImportFaculties.sendFile)
async def import_faculties(message: Message):
    tuid = message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(message.message_id)
    await delete_previous_messages(message, tuid)
    try:
        # Получаем ID файла и информацию о нём
        file_id = message.document.file_id
        file_info = await message.bot.get_file(file_id)

        # Определяем путь для сохранения файла
        file_path = os.path.join(os.getcwd(), message.document.file_name)

        # Скачиваем файл по предоставленному Telegram URL
        file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file_info.file_path}"
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                if response.status == 200:
                    with open(file_path, 'wb') as f:
                        f.write(await response.read())
                else:
                    await message.answer("Не удалось скачать файл. Проверьте правильность загрузки.",
                                         reply_markup=kb.go_to_admin)
                    return

        # Импортируем данные в БД
        result = await rq.import_faculties_from_excel(filename=file_path)

        # Удаляем файл после обработки
        os.remove(file_path)

        # Отправляем результат пользователю
        await message.answer(result,
                             reply_markup=kb.go_to_admin)
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")

@router.callback_query(F.data == 'manage_deportment')
async def manage_department(callback: CallbackQuery):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(callback.message.message_id)
    await delete_previous_messages(callback.message, tuid)

    sent_message = await callback.message.answer_photo(
        photo=utils.adminManagePicture,
        caption="Вы можете экспортировать все данные о кафедрах в формате Excel."
                "\nМожете импортировать данные из файла Excel в БД",
        reply_markup=kb.manage_departments
    )

    user_data['bot_messages'].append(sent_message.message_id)

@router.callback_query(F.data == 'export_department')
async def export_department(callback: CallbackQuery, state: FSMContext):
    try:
        tuid = callback.message.chat.id
        user_data = sent_message_add_screen_ids[tuid]
        user_data['user_messages'].append(callback.message.message_id)
        await delete_previous_messages(callback.message, tuid)

        filename = os.path.join(os.getcwd(), "departments.xlsx")
        is_generate = await rq.export_departments_to_excel(filename=filename)

        if is_generate:
            if os.path.exists(filename):
                file = FSInputFile(filename)
                sent_message = await callback.message.answer_document(
                    document=file,
                    caption="Готово! Вот данные кафедр.",
                    reply_markup=kb.go_to_admin
                )
                user_data['bot_messages'].append(sent_message.message_id)
                os.remove(filename)
            else:
                await callback.message.answer("Файл не найден после генерации.",
                                              reply_markup=kb.go_to_admin)
        else:
            sent_message = await callback.message.answer(
                "Ошибка при создании файла. Данные отсутствуют.",
                reply_markup=kb.go_to_admin
            )
            user_data['bot_messages'].append(sent_message.message_id)
    except Exception as e:
        print(f"Error in export_department: {e}")
        await callback.message.answer("Произошла ошибка. Попробуйте еще раз.",
                                      reply_markup=kb.go_to_admin)

@router.callback_query(F.data == 'import_department')
async def import_departments(callback: CallbackQuery, state: FSMContext):
    tuid = callback.message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(callback.message.message_id)
    await delete_previous_messages(callback.message, tuid)
    sent_message = await callback.message.answer(
        "Отправьте файл в формате Excel.",
    )
    user_data['bot_messages'].append(sent_message.message_id)
    await state.set_state(st.ImportDepartments.sendFile)


@router.message(st.ImportDepartments.sendFile)
async def import_departments(message: Message):
    tuid = message.chat.id
    user_data = sent_message_add_screen_ids[tuid]
    user_data['user_messages'].append(message.message_id)
    await delete_previous_messages(message, tuid)
    try:
        file_id = message.document.file_id
        file_info = await message.bot.get_file(file_id)
        file_path = os.path.join(os.getcwd(), message.document.file_name)
        file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file_info.file_path}"
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                if response.status == 200:
                    with open(file_path, 'wb') as f:
                        f.write(await response.read())
                else:
                    await message.answer("Не удалось скачать файл. Проверьте правильность загрузки.",
                        reply_markup=kb.go_to_admin)
                    return

        result = await rq.import_departments_from_excel(filename=file_path)
        os.remove(file_path)
        await message.answer(result,
                             reply_markup=kb.go_to_admin)
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")
