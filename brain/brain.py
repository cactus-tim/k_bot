import json

from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from openai import OpenAI
import os
import re
from dotenv import load_dotenv
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.handlers.errors import safe_send_message
from bot.handlers.questionary import update_def_part_1
from database.req import get_user, update_user, get_dialog, create_dialog, update_dialog, create_thread
from hands.hands import mamba_parsing_dialogs
from instance import client, bot
from errors.error_handlers import gpt_error_handler
from errors.errors import ContentError, FileError, NumberError


async def is_number_in_range(s):
    try:
        num = float(s)
        return 1 <= num <= 10
    except ValueError:
        return False


@gpt_error_handler
async def gpt_assystent_mes(thread_id, assistant_id, mes="давай начнем"):
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=mes
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )

    messages = client.beta.threads.messages.list(thread_id=thread_id)
    data = messages.data[0].content[0].text.value.strip()
    if not data:
        raise ContentError
    else:
        return data


async def check_dialog(dialog_id, user_id):
    dialog = await get_dialog(dialog_id)
    if dialog == "not created":
        await create_dialog(dialog_id, user_id)
        dialog = await get_dialog(dialog_id)
    if dialog.status == "banned" or dialog.status == "banned":
        return False
    return True


@gpt_error_handler
async def get_dialog_in_json(dialog_id):
    dialog = await get_dialog(dialog_id)
    messages = client.beta.threads.messages.list(thread_id=dialog.thread_brain)
    data = {'messages': []}
    for mes in messages.data:
        data['messages'].append({'sender': ("собеседник" if mes.role == "user" else "пользователь"),
                                 'text': mes.content[0].text.value.strip()})
    return data


@gpt_error_handler
async def send_dialog_to_user(dialog_id, rate):
    dialog = await get_dialog(dialog_id)
    to_summary = await get_dialog_in_json(dialog_id)
    msg = f"""
    Привет! Нашли новое хорошее знакомство!
    Ссылка на диалог https://www.mamba.ru/chats/{dialog_id}/contact
    Моя оценка - {rate}
    Краткое саммари диалога:
    
    """
    thread_id = await create_thread()
    msg += await gpt_assystent_mes(thread_id, 'asst_jaWzTvMtkraZtmPSc2FR2oQV', str(to_summary))
    await safe_send_message(bot, dialog.user_id, "")


@gpt_error_handler
async def read_msg(dialog_id, msg):
    dialog = await get_dialog(dialog_id)
    user = await get_user(dialog.user_id)
    for m in msg.split('\n'):
        ans = await gpt_assystent_mes(dialog_id.thread_def, user.def_id, m)
        if not is_number_in_range(ans):
            raise NumberError(dialog.user_id, dialog_id)
        rate = int(ans)
        if 5 <= rate <= 7:
            storage = MemoryStorage()
            storage_key = StorageKey(bot_id=bot.id, chat_id=dialog.user_id, user_id=dialog.user_id)
            state = FSMContext(storage=storage, key=storage_key)
            await update_def_part_1(dialog.user_id, msg, rate, state)
            continue
        elif rate < 5:
            continue
        else:
            await update_dialog(dialog_id, {"status": "banned"})
            return False
    return True


@gpt_error_handler
async def write_msg(dialog_id, msg):
    dialog = await get_dialog(dialog_id)
    user = await get_user(dialog.user_id)
    ans = ''
    for m in msg.split('\n'):
        temp_ans: str = await gpt_assystent_mes(dialog_id.thread_brain, user.brain_id, m)
        i = temp_ans.lower().find("готово")
        if i != -1:
            rate_row = temp_ans[i+7]
            if not is_number_in_range(rate_row):
                raise NumberError(dialog.user_id, dialog_id)
            rate = int(rate_row)
            if rate <= 5:
                await update_dialog(dialog_id, {"status": "banned"})
                return False, ''
            else:
                await send_dialog_to_user(dialog_id, rate)
                await update_dialog(dialog_id, {"status": "approved"})
                ans += temp_ans[:i] + '\n' + temp_ans[i+9:]
                return True, ans
        else:
            ans += temp_ans
    return True, ans
