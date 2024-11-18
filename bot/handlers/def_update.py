from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

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


class UpdateDefState(StatesGroup):
    waiting_user_op = State()


async def update_def_part_1(user_id, mes, rate, state: FSMContext):
    message = (f"Я получила вот такое сообщение от ползователя:\n\n{mes}\n\n"
               f"Я его оцниваю как {rate} по шкале от 1 до 10, где 10 - полное соответсвие твоей системе ред флагов\n"
               f"А что думаешь ты?\n"
               f"Оцени его от 1 до 10 и отправь мне только число")
    await safe_send_message(bot, user_id, message)
    await state.update_data({
        'mes': mes,
        'rate': rate
    })
    await state.set_state(UpdateDefState.waiting_user_op)


@router.message(UpdateDefState.waiting_user_op)
async def update_def_part_2(message: Message, state: FSMContext):
    if not is_number_in_range(message.text):
        await safe_send_message(bot, message, "Можно отправить только число от 1 до 10!")
        return
    data = await state.get_data()
    mes = data.get("mes")
    rate = data.get("rate")
    await update_def(message.from_user.id, mes, rate, int(message.text))
    await safe_send_message(bot, message, "Спасибо!")
    await state.clear()