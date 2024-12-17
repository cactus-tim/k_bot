from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from database.req import get_dialog, get_upd, create_upd_wait, create_upd, del_upd, get_upd_wait, del_upd_wait
from instance import bot
from bot.handlers.errors import safe_send_message
from brains.create_brain import update_def


router = Router()


async def is_number_in_range(s):
    try:
        num = float(s)
        return 1 <= num <= 10
    except ValueError:
        return False


async def trigger_update_def_part_1(user_id, msg, rate):
    await update_def_part_1(user_id, msg, rate)


class UpdateDefState(StatesGroup):
    waiting_user_op = State()


async def update_def_part_1(user_id, mes, rate):
    # как изменить: попробуй просто отправлять сообщение, а вот дату вметсо переменной состояния закидывать в бдшку
    # и там уже что то можно придумать (из лиды знаем как такие записи извлекать из бд,
    # и как раз по этой логике дергать обновление)
    upd = await get_upd(user_id)
    if upd:
        await create_upd_wait(user_id, mes, rate)
    else:
        message = (f"Я получила вот такое сообщение от ползователя:\n\n{mes}\n\n"
                   f"Я его оцниваю как {rate} по шкале от 1 до 10, где 10 - полное соответсвие твоей системе ред флагов\n"
                   f"А что думаешь ты?\n"
                   f"Оцени его от 1 до 10 и отправь мне только число")
        await safe_send_message(bot, user_id, message)
        await create_upd(user_id, mes, rate)


@router.message()
async def update_def_part_2(message: Message):
    upd = await get_upd(message.from_user.id)
    if not upd:
        return
    if not is_number_in_range(message.text):
        await safe_send_message(bot, message, "Можно отправить только число от 1 до 10!")
        return
    mes = upd.mes
    rate = upd.rate
    await update_def(message.from_user.id, mes, rate, int(message.text))
    await safe_send_message(bot, message, "Спасибо!")
    await del_upd(message.from_user.id)
    upd_wait = await get_upd_wait(message.from_user.id)
    if upd_wait:
        await del_upd_wait(upd_wait.id)
        await update_def_part_1(message.from_user.id, upd_wait.mes, upd_wait.rate)

