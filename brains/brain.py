import json
from openai import OpenAI
import os
import re
from dotenv import load_dotenv
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.handlers.errors import safe_send_message
from database.req import get_user, update_user, get_dialog, create_dialog, update_dialog, create_thread
from bot.handlers.def_update import update_def_part_1, trigger_update_def_part_1
from instance import client, bot
from bot.handlers.errors import gpt_error_handler
from bot.handlers.errors import gpt_assystent_mes
from errors.errors import ContentError, FileError, NumberError


async def is_number_in_range(s):
    try:
        num = float(s)
        return 1 <= num <= 10
    except ValueError:
        return False

# 483458201,Тима.,"",asst_GGgV1EmufFpvznAIv7JUpDpf,asst_jgpGLwFfqM4IciACwM0HBFZJ,thread_WwexkrdWJggDAMCRsYz9YQyi,thread_TTnNts6PM5AKmZBVJJDW4cFC,{Mamba},"",true,true,true,true
# 3,483458201,1,mamba,lida.aiseller@gmail.com,T37RrMDT
# 1,gggg:gggg,0,0,true


async def check_dialog(dialog_id, user_id):
    dialog = await get_dialog(dialog_id)
    if dialog == "not created":
        await create_dialog(dialog_id, user_id)
        dialog = await get_dialog(dialog_id)
    if dialog.status == "banned" or dialog.status == "approved":
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
    await safe_send_message(bot, dialog.user_id, msg)


@gpt_error_handler
async def read_msg(dialog_id, msg):
    dialog = await get_dialog(dialog_id)
    user = await get_user(dialog.user_id)
    for m in msg.split('\n'):
        if m == '':
            break
        ans = await gpt_assystent_mes(dialog.thread_def, user.def_id, m)
        if not await is_number_in_range(ans):
            raise NumberError(dialog.user_id, dialog_id)
        rate = int(ans)
        if 5 <= rate <= 7:
            # await trigger_update_def_part_1(dialog.user_id, msg, rate)
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
        if m == '':
            break
        temp_ans: str = await gpt_assystent_mes(dialog.thread_brain, user.brain_id, m)
        i = temp_ans.lower().find("готово")
        if i != -1:
            rate_row = temp_ans[i+7]
            if not await is_number_in_range(rate_row):
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
