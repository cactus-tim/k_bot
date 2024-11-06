from aiogram.filters import Command, CommandStart
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.handlers.errors import safe_send_message
from instance import bot
from bot.keyboards.keyboards import get_main_ikb, check_ability, get_services_kb, get_services_update_kb
from database.req import create_user, get_user, update_user, create_acc, update_acc, del_acc, \
    create_proxy, del_proxy

router = Router()


class AddProxyState(StatesGroup):
    waiting_proxy = State()


@router.message(Command("add_proxy"))
async def cmd_add_proxy(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user.is_superuser:
        return
    await safe_send_message(bot, message, "Отправьте новый прокси")
    await state.set_state(AddProxyState.waiting_proxy)


@router.message(AddProxyState.waiting_proxy)
async def processing_add_proxy(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user.is_superuser:
        return
    await create_proxy(message.text)
    await safe_send_message(bot, message, "Прокси добавлено")
    await state.clear()


class DelProxyState(StatesGroup):
    waiting_proxy = State()


@router.message(Command("add_proxy"))
async def cmd_add_proxy(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user.is_superuser:
        return
    await safe_send_message(bot, message, "Отправьте прокси который надо удалить")
    await state.set_state(DelProxyState.waiting_proxy)


@router.message(DelProxyState.waiting_proxy)
async def processing_add_proxy(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user.is_superuser:
        return
    if await del_proxy(message.text) != 'ok':
        await safe_send_message(bot, message, "Что то пошло не так, попробуйте позже")
    else:
        await safe_send_message(bot, message, "Прокси удален")
    await state.clear()
