from aiogram import Router, F
from aiogram.filters import Command
import io
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards.keyboards import get_new_data_kb, get_add_data_kb, get_end_add_kb
from instance import bot, client
from database.req import get_user, update_user
from bot.handlers.errors import safe_send_message
from database.models import User
from brain.create_brain import gpt_assystent_mes, create_brain, create_def, update_def, update_data

router = Router()


async def clean_prompt(prompt):  # TODO: need to check
    start = prompt.find("{")
    end = prompt.find("}")
    result = prompt[start+1:end]
    return result


async def is_number_in_range(s):
    try:
        num = float(s)
        return 1 <= num <= 10
    except ValueError:
        return False


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


class QuestState(StatesGroup):
    waiting_add_data_choice = State()
    add_quset = State()
    waiting_new_data_choice = State()
    first_quest = State()
    second_quest = State()
    finish_quest = State()


@router.message(Command("update_data"))
async def update_data_part_1(message: Message, state: FSMContext):
    await safe_send_message(bot, message, "Какую часть опроса вы хотите дополнить?", reply_markup=get_add_data_kb())
    await state.set_state(QuestState.waiting_add_data_choice)


@router.message(QuestState.waiting_add_data_choice)
async def update_data_part_2(message: Message, state: FSMContext):  # TODO: test ass_up
    user = await get_user(message.from_user.id)
    if message.text == "Первую":
        ass_id = user.brain_id
        thread_id = user.thread_q1
    elif message.text == "Вторую":
        ass_id = user.def_id
        thread_id = user.thread_q2
        await state.update_data({'is_q2': True})
    else:
        await safe_send_message(bot, message, "Надо нажать на кнопку")
        return
    await state.update_data({'ass_to_up': ass_id, 'thread_to_up': thread_id})
    f_m = await gpt_assystent_mes(thread_id, assistant_id=ass_id, mes="Сейчас я внесу пару корректировок, как только "
                                                                      "я напишу 'готово', отправь мне обновленный "
                                                                      "промпт")
    await safe_send_message(bot, message, f_m)
    await state.set_state(QuestState.add_quset)


@router.message(QuestState.add_quset)
async def update_data_part_3_gpt(message: Message, state: FSMContext):
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

    data = await state.get_data()
    ass_id = data.get("ass_to_up")
    thread_id = data.get("thread_to_up")
    flag = data.get("is_q2")
    if user_message.lower().strip() == "готово":
        mes = await gpt_assystent_mes(thread_id, ass_id, user_message)
        new_prompt = await clean_prompt(mes)
        await update_data(ass_id, new_prompt, flag)
        await safe_send_message(bot, message, "Донастраиваем ИИ под вас.")
        await state.set_state(QuestState.finish_quest)
    else:
        mes = await gpt_assystent_mes(thread_id, ass_id, user_message)
        await safe_send_message(bot, message, mes, reply_markup=get_end_add_kb())


@router.message(Command("new_data"))
async def get_new_thread(message: Message, state: FSMContext):
    await safe_send_message(bot, message, "Какую часть опроса вы хотите перепройти", reply_markup=get_new_data_kb())
    await state.set_state(QuestState.waiting_new_data_choice)


@router.message(QuestState.waiting_new_data_choice)
async def give_new_thread(message: Message, state: FSMContext):
    if message.text == "Первую" or message.text == "Обе":
        user = await get_user(message.from_user.id)
        if not check_services_good(user):
            return
        thread = client.beta.threads.create()
        thread_id = thread.id
        await update_user(user.id, {'thread_q1': thread_id})
        f_m = await gpt_assystent_mes(thread_id, assistant_id='')
        await safe_send_message(bot, message, f_m)
        if message.text == "Первую":
            await state.update_data({'only_one': True})
        await state.set_state(QuestState.first_quest)
    elif message.text == "Вторую":
        await state.set_state(QuestState.second_quest)
    else:
        await safe_send_message(bot, message, "Надо нажать на кнопку")


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
        data = await state.get_data()
        if data.get("only_one"):
            await state.update_data({'only_one': False})
            await state.set_state(QuestState.finish_quest)
        else:
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
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)  # TODO: need to test
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
