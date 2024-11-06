from aiogram import Router, F

from instance import bot
from database.req import get_user, update_user
from bot.handlers.errors import safe_send_message
from database.models import User

router = Router()


async def check_services_good(user: User):
    if user.cur_service != '':
        await safe_send_message(bot, user.id,
                                text=f"Вы не закончили добавление аккаунта от сервиса {user.cur_service}."
                                     "\nПожалуста, пройдите эту процедуру заново.\n"
                                     "Для этого введите /add_acc"
                                     "А затем продолжите регистрацию, для этого нажмите /start")
        return None
    else:
        return "ok"


@router.callback_query(F.data == "data")
async def start_query(callback: F.CallbackQuery):
    # await callback.message.delete()
    user = await get_user(callback.from_user.id)
    if not check_services_good(user):
        return
    thread = client.beta.threads.create()
    thread_id = thread.id
    await update_user(user.id, {'questing': True, 'thread': thread_id})
    # TODO: implemet here rest of func
