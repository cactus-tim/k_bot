from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.types import Message

from bot.errors import safe_send_message
from instance import bot
from bot.keyboards.keyboards import get_main_ikb, get_services_ikb, check_ability
from database.req import create_user, get_user, update_user, create_acc, update_acc, get_acc_by_service

router = Router()


async def check_rightness(login: str, password: str) -> bool:  # TODO: add regexp for login and password
    if not login:
        return False
    if not password:
        return False
    return True


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if user == "not created":
        await create_user(message.from_user.id)
    await safe_send_message(bot, message, text="Привет!\nМеня зовут K_bot и я помогу найти тебе пару.\n"
                                               "Для начала нажми кнопку внизу сообщения что бы я узнал тебя поближе, "
                                               "после чего мы начнем)",  # TODO: rewrite start message
                            reply_markup=get_main_ikb())


@router.message(Command("info"))
async def cmd_info(message: Message):
    await safe_send_message(bot, message, text="Я учусь и уже кое-что могу: ежедневно вместо вас я буду общаться с "
                                               "потенциальеыми парами на сайтах знакомств.\n"
                                               "Если я пойму, что тот с кем я общаюсь достоен встречи с вами, "
                                               "я предложу ему ним встретится и пришлю вам информацию о нем, "
                                               "саммари диалога и ссылку на него.",  # TODO: rewrite info message
                            reply_markup=get_main_ikb())


@router.message(Command("add_acc"))
async def add_acc(message: Message):
    user = await get_user(message.from_user.id)
    if user == "not created":
        await create_user(message.from_user.id)
    if await check_ability(len(user.services)):
        await safe_send_message(bot, message, text="Вы уже добавили аккуанты всех сервисов с которыми мы работаем.")
    else:
        await safe_send_message(bot, message, text="Выбери сервис, аккаунт которого ты хочешь добавить:",  # TODO: rewrite add_acc message
                                reply_markup=get_services_ikb(user))


@router.callback_query(F.data in ["mamba"])  # you can add here more callback data with services names
async def add_acc_part_2(callback: F.CallbackQuery):
    await update_user(callback.from_user.id, {'cur_service': callback.data})
    await create_acc(callback.from_user.id, callback.data)
    await safe_send_message(bot, callback, text="Теперь отправьте логин от аккаунта в формате.\n"
                                               "Логин:*ваш логин*")


@router.message(F.message.text.func(lambda text: "логин" in text.lower()))  # TODO: check rightness
async def add_acc_part_3(message: Message):
    user = await get_user(message.from_user.id)
    await update_acc(message.from_user.id, user.cur_service, {"login": message.text[6:].strip()})
    await safe_send_message(bot, message, text="Теперь отправьте пароль от аккаунта в формате.\n"
                                               "Пароль:*ваш пароль*")


@router.message(F.message.text.func(lambda text: "пароль" in text.lower()))  # TODO: check rightness
async def add_acc_part_4(message: Message):
    user = await get_user(message.from_user.id)
    await update_acc(message.from_user.id, user.cur_service, {"password": message.text[7:].strip()})
    acc = await get_acc_by_service()
    if await check_rightness(acc.login, acc.password):
        await safe_send_message(bot, message, text="Все отлично, аккаунт добавлен.")
        await update_user(message.from_user.id, {'cur_service': ''})
    else:
        await safe_send_message(bot, message, text="Что то пошло не так, попробуйте еще раз.")
        # TODO: in future if user sand message block it and sand him here


async def update_acc_part_1(message: Message):
    pass
