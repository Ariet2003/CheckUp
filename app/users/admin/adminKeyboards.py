from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database import requests as rq

admin_account = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🛠️ Управление", callback_data="admin_manage"),
     InlineKeyboardButton(text="👥 Пользователи", callback_data="view_user")],
    [InlineKeyboardButton(text="📜 Отчет", callback_data="generate_report"),
     InlineKeyboardButton(text="📈 Статистика", callback_data="view_statistics")]
])

view_users = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➕ Преподавателя", callback_data="add_teacher"),
     InlineKeyboardButton(text="➖ Преподавателя", callback_data="delete_teacher")],
    [InlineKeyboardButton(text="➕ Администратора", callback_data="add_admin"),
     InlineKeyboardButton(text="➖ Администратора", callback_data="delete_admin")],
    [InlineKeyboardButton(text="📄 Преподаватели", callback_data="list_teacher"),
     InlineKeyboardButton(text="📄 Администраторы", callback_data="list_admin")],
    [InlineKeyboardButton(text="⬅️ Личный кабинет", callback_data="go_home_admin")]
])

go_to_admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⬅️ Личный кабинет", callback_data="go_home_admin")]
])

def deleting_confirmation(telegram_id: str):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data=f'delete_admin_{telegram_id}'),
         InlineKeyboardButton(text="Нет", callback_data='go_home_admin')],
        [InlineKeyboardButton(text="⬅️ Личный кабинет", callback_data="go_home_admin")]
    ])
    return keyboard

def deleting_confirmation_teacher(telegram_id: str):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data=f'delete_teacher_{telegram_id}'),
         InlineKeyboardButton(text="Нет", callback_data='go_home_admin')],
        [InlineKeyboardButton(text="⬅️ Личный кабинет", callback_data="go_home_admin")]
    ])
    return keyboard

export_teacher = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📥 Экспорт", callback_data="export_teacher")],
    [InlineKeyboardButton(text="⬅️ Личный кабинет", callback_data="go_home_admin")]
])

export_admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📥 Экспорт", callback_data="export_admin")],
    [InlineKeyboardButton(text="⬅️ Личный кабинет", callback_data="go_home_admin")]
])

manage_admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👥 Студенты", callback_data="manage_students"),
     InlineKeyboardButton(text="📅 Расписание", callback_data="manage_schedule")],
    [InlineKeyboardButton(text="📜 Группы", callback_data="manage_group"),
     InlineKeyboardButton(text="🔰 Курсы", callback_data="manage_course")],
    [InlineKeyboardButton(text="🔰 Факультеты", callback_data="manage_faculty"),
     InlineKeyboardButton(text="🔰 Кафедры", callback_data="manage_deportment")],
    [InlineKeyboardButton(text="⬅️ Личный кабинет", callback_data="go_home_admin")]
])

manage_faculties = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📥 Экспорт", callback_data="export_faculty"),
     InlineKeyboardButton(text="📤 Импорт", callback_data="import_faculty")],
    [InlineKeyboardButton(text="⬅️ Личный кабинет", callback_data="go_home_admin")]
])