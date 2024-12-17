from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from database.req import get_user
from database.models import User

services = [
    "Mamba",
]


def get_main_ikb() -> InlineKeyboardMarkup:
    ikb = [
        [InlineKeyboardButton(text="Начать заполнять данные", callback_data="data")],
    ]
    ikeyboard = InlineKeyboardMarkup(inline_keyboard=ikb)
    return ikeyboard


def check_ability(len_user_list: int):
    return True if len_user_list == len(services) else False


def get_services_ikb(user: User) -> InlineKeyboardMarkup:
    ikb = [[InlineKeyboardButton(text=service, callback_data=service.lower())] for service in services if service not in user.services]
    ikeyboard = InlineKeyboardMarkup(inline_keyboard=ikb)
    return ikeyboard


def get_services_kb(user: User) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=service)] for service in services if service not in user.services],
        resize_keyboard=True
    )
    return keyboard


def get_services_update_ikb(user: User) -> InlineKeyboardMarkup:
    ikb = [[InlineKeyboardButton(text=service, callback_data=service.lower())] for service in services if service in user.services]
    ikeyboard = InlineKeyboardMarkup(inline_keyboard=ikb)
    return ikeyboard


def get_services_update_kb(user: User) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=service)] for service in services if service in user.services],
        resize_keyboard=True
    )
    return keyboard


def get_new_data_kb() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Первую"), KeyboardButton(text="Вторую"), KeyboardButton(text="Обе")]],
        resize_keyboard=True
    )
    return keyboard


def get_add_data_kb() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Первую"), KeyboardButton(text="Вторую")]],
        resize_keyboard=True
    )
    return keyboard


def get_end_add_kb() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Готово")]],
        resize_keyboard=True
    )
    return keyboard
