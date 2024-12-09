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
    [InlineKeyboardButton(text="⬅️ Личный кабинет", callback_data="go_home_admin")]
])

go_to_admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⬅️ Личный кабинет", callback_data="go_home_admin")]
])