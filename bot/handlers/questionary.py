from aiogram import Router, F
import io
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


from instance import bot, client
from database.req import get_user, update_user
from bot.handlers.errors import safe_send_message
from database.models import User
from brain.create_brain import gpt_assystent_mes, create_brain, create_def

router = Router()


class QuestState(StatesGroup):
    first_quest = State()
    second_quest = State()
    finish_quest = State()


async def clean_prompt(prompt):  # TODO: need to check
    start = prompt.find("{")
    end = prompt.find("}")
    result = prompt[start+1:end]
    return result


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
async def start_query(callback: F.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    user = await get_user(callback.from_user.id)
    if not check_services_good(user):
        return
    if user.thread_q1 == '':
        thread = client.beta.threads.create()
        thread_id = thread.id
        await update_user(user.id, {'thread_q1': thread_id})
    else:
        thread_id = user.thread_q1

    f_m = await gpt_assystent_mes(thread_id, assistant_id='')
    await safe_send_message(bot, callback, f_m)
    await state.set_state(QuestState.first_quest)


@router.message(QuestState.first_quest)
async def gpt_handler_first(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await get_user(user_id)
    if message.voice:
        voice_file = io.BytesIO()
        voice_file_id = message.voice.file_id
        file = await bot.get_file(voice_file_id)
        await bot.download_file(file.file_path, voice_file)
        voice_file.seek(0)
        voice_file.name = "voice_message.ogg"

        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=voice_file,
            response_format="text"
        )
        user_message = transcription
    elif message.text:
        user_message = message.text
    else:
        return
    thread_id = await user.thread_q1
    msg = await gpt_assystent_mes(thread_id, '', user_message)
    break_state = msg.find('{') + msg.find('}') != -2
    if break_state:
        prompt = await clean_prompt(msg)
        await create_brain(user_id, prompt)
        await safe_send_message(bot, message, "Отлично, мы собрали необходимую информацию!\n"
                                              "Настраиваем ИИ под вас.")
        await state.update_data({'first': True})
        await state.set_state(QuestState.second_quest)
    else:
        await safe_send_message(bot, message, msg)


@router.message(QuestState.second_quest)
async def gpt_handler_second(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await get_user(user_id)
    data = await state.get_data()
    flag = data.get("first")
    if flag:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)  # TODO: need to test
        if user.thread_q2 == '':
            thread = client.beta.threads.create()
            thread_id = thread.id
            await update_user(user.id, {'thread_q2': thread_id})
        else:
            thread_id = user.thread_q2

        thread_name = client.beta.threads.create()
        name = await gpt_assystent_mes(thread_name.id, user.brain_id, "Как тебя зовут? Напиши только имя, больше ничего")
        await update_user(user_id, {"name": name})
        f_m = await gpt_assystent_mes(thread_id, assistant_id='', mes=f"Давай начнем, ты будешь общаться с {name}")
        await safe_send_message(bot, message, f_m)
        await state.update_data({'first': False})
        return

    if message.voice:
        voice_file = io.BytesIO()
        voice_file_id = message.voice.file_id
        file = await bot.get_file(voice_file_id)
        await bot.download_file(file.file_path, voice_file)
        voice_file.seek(0)
        voice_file.name = "voice_message.ogg"

        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=voice_file,
            response_format="text"
        )
        user_message = transcription
    elif message.text:
        user_message = message.text
    else:
        return
    thread_id = await user.thread_q2
    msg = await gpt_assystent_mes(thread_id, '', user_message)
    break_state = msg.find('{') + msg.find('}') != -2
    if break_state:
        prompt = await clean_prompt(msg)
        await create_def(user_id, prompt)
        await safe_send_message(bot, message, "Отлично, мы собрали необходимую информацию!\n"
                                              "Донастраиваем ИИ под вас.")
        await state.set_state(QuestState.finish_quest)
    else:
        await safe_send_message(bot, message, msg)


@router.message(QuestState.finish_quest)
async def gpt_handler_finish(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if user.brain_id == '' or not user.is_quested1:
        await safe_send_message(bot, message, "надо перепройти первую часть анкеты, там что то пошло не по плану")
        await state.set_state(QuestState.first_quest)
    elif user.def_id == '' or not user.is_quested2:
        await safe_send_message(bot, message, "надо перепройти вторую часть анкеты, там что то пошло не по плану")
        await state.set_state(QuestState.second_quest)
    else:
        await safe_send_message(bot, message, "все круто")
        await state.clear()
