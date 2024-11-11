from aiogram.filters import Command, CommandStart
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.handlers.errors import safe_send_message
from instance import bot
from bot.keyboards.keyboards import get_main_ikb, check_ability, get_services_kb, get_services_update_kb
from database.req import create_user, get_user, update_user, create_acc, update_acc, del_acc, \
    get_acc

router = Router()


async def check_rightness(login: str, password: str) -> bool:  # TODO: add regexp for login and password
    if not login:
        return False
    if not password:
        return False
    return True


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await get_user(message.from_user.id)
    if user == "not created":
        await create_user(message.from_user.id)
    await safe_send_message(bot, message, text="Привет!\nМеня зовут K_bot и я помогу найти тебе пару.\n"
                                               "Для начала нажми кнопку внизу сообщения что бы я узнал тебя поближе, "
                                               "после чего мы начнем)",  # TODO: rewrite start message
                            reply_markup=get_main_ikb())


@router.message(Command("info"))
async def cmd_info(message: Message):
    user = await get_user(message.from_user.id)
    if user.is_superuser:
        await safe_send_message(bot, message, text="/start\n"
                                                   "/info\n"
                                                   "/add_acc\n"
                                                   "/update_acc\n"
                                                   "/del_acc\n"
                                                   "/add_proxy\n"
                                                   "/del_proxy\n")
    else:
        await safe_send_message(bot, message, text="/start\n"
                                                   "/info\n"
                                                   "/add_acc\n"
                                                   "/update_acc\n"
                                                   "/del_acc\n",
                                reply_markup=get_main_ikb())


class AccState(StatesGroup):
    waiting_service = State()
    waiting_mail = State()
    waiting_password = State()


@router.message(Command("add_acc"))
async def add_acc(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if check_ability(len(user.services)):
        await safe_send_message(bot, message, text="Вы уже добавили аккуанты всех сервисов с которыми мы работаем.")
    else:
        await safe_send_message(bot, message, text="Выбери сервис, аккаунт которого ты хочешь добавить:",  # TODO: rewrite add_acc message
                                reply_markup=get_services_kb(user))
    await state.set_state(AccState.waiting_service)


# @router.callback_query(F.data in ["mamba"])  # you can add here more callback data with services names
@router.message(AccState.waiting_service)
async def add_acc_part_2(message: Message, state: FSMContext):
    await update_user(message.from_user.id, {'cur_service': message.text})
    await create_acc(message.from_user.id, message.text)
    await safe_send_message(bot, message, text="Теперь отправьте логин от аккаунта в формате.\n"
                                               "Логин:*ваш логин*")
    await state.set_state(AccState.waiting_mail)


@router.message(AccState.waiting_mail)
async def add_acc_part_3(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    login = message.text[6:].strip() if message.text[:6].strip() == 'Пароль:' else message.text.strip()
    await update_acc(message.from_user.id, user.cur_service, {"login": login})
    await safe_send_message(bot, message, text="Теперь отправьте пароль от аккаунта в формате.\n"
                                               "Пароль:*ваш пароль*")
    await state.set_state(AccState.waiting_password)


@router.message(AccState.waiting_password)
async def add_acc_part_4(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    password = message.text[7:].strip() if message.text[:7].strip() == 'Пароль:' else message.text
    await update_acc(message.from_user.id, user.cur_service, {"password": password})
    acc = await get_acc(message.from_user.id, user.cur_service)
    if await check_rightness(acc.login, acc.password):
        await safe_send_message(bot, message, text="Все отлично, аккаунт добавлен.")
        services = user.services
        services.append(user.cur_service)
        await update_user(message.from_user.id, {'cur_service': '', 'services': services})
    else:
        await safe_send_message(bot, message, text="Что то пошло не так, попробуйте еще раз.")
    await state.clear()


class AccUpdateState(StatesGroup):
    waiting_service = State()
    waiting_password = State()


@router.message(Command("update_acc"))
async def update_acc_part_1(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if len(user.services) == 0:
        await safe_send_message(bot, message, text="У вас нет подключенных сервисов")
    else:
        await safe_send_message(bot, message, text="Выбери сервис, пароль от которого ты хочешь изменить:",
                                    # TODO: rewrite add_acc message
                                    reply_markup=get_services_update_kb(user))
    await state.set_state(AccUpdateState.waiting_service)


@router.message(AccUpdateState.waiting_service)
async def update_acc_part_2(message: Message, state: FSMContext):
    await update_user(message.from_user.id, {'cur_service': message.text})
    await safe_send_message(bot, message, text="Теперь отправьте новый пароль от аккаунта в формате.\n"
                                               "Пароль:*ваш пароль*")
    await state.set_state(AccUpdateState.waiting_password)


@router.message(AccUpdateState.waiting_password)
async def update_acc_part_3(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    password = message.text[7:].strip() if message.text[:7].strip() == 'Пароль:' else message.text
    await update_acc(message.from_user.id, user.cur_service, {"password": password})
    acc = await get_acc(message.from_user.id, user.cur_service)
    if await check_rightness(acc.login, acc.password):
        await safe_send_message(bot, message, text="Все отлично, пароль изменен.")
        await update_user(message.from_user.id, {'cur_service': ''})
        await state.clear()
    else:
        await safe_send_message(bot, message, text="Что то пошло не так, отправьте пароль еще раз.")


class AccDelState(StatesGroup):
    waiting_service = State()


@router.message(Command("del_acc"))
async def del_acc_part_1(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if len(user.services) == 0:
        await safe_send_message(bot, message, text="У вас нет подключенных сервисов")
    else:
        await safe_send_message(bot, message, text="Выбери сервис, аккаунт которого ты хочешь добавить:",
                                # TODO: rewrite add_acc message
                                reply_markup=get_services_update_kb(user))
    await state.set_state(AccDelState.waiting_service)


@router.message(AccDelState.waiting_service)
async def update_acc_part_2(message: Message, state: FSMContext):
    if await del_acc(message.from_user.id, message.text) != 'ok':
        await safe_send_message(bot, message, "Что то пошло не так, попробуйте позже")
    else:
        user = await get_user(message.from_user.id)
        new_services = user.services
        new_services.remove(message.text)
        await update_user(message.from_user.id, {'services': new_services})
        await safe_send_message(bot, message, text="Аккаунт успешно удален")
    await state.clear()


@router.message(Command("new_data"))
async def get_new_thread(message: Message):
    pass
