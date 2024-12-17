from aiogram import Router, types, Bot
import asyncio
from aiogram.types import ReplyKeyboardRemove, Message
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter, TelegramUnauthorizedError, TelegramNetworkError
from functools import wraps
import asyncio
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException, ElementNotInteractableException
from openai import AuthenticationError, RateLimitError, APIConnectionError, APIError
from aiohttp import ClientError
from asyncio import TimeoutError

from errors.errors import ContentError
from instance import logger, bot, client
from aiohttp import ClientConnectorError
from errors.errors import *


router = Router()


@router.errors()
async def global_error_handler(update: types.Update, exception: Exception):
    if isinstance(exception, TelegramBadRequest):
        logger.error(f"Некорректный запрос: {exception}. Пользователь: {update.message.from_user.id}")
        return True
    elif isinstance(exception, TelegramRetryAfter):
        logger.error(f"Request limit exceeded. Retry after {exception.retry_after} seconds.")
        await asyncio.sleep(exception.retry_after)
        return True
    elif isinstance(exception, TelegramUnauthorizedError):
        logger.error(f"Authorization error: {exception}")
        return True
    elif isinstance(exception, TelegramNetworkError):
        logger.error(f"Network error: {exception}")
        await asyncio.sleep(5)
        await safe_send_message(bot, update.message.chat.id, text="Повторная попытка...")
        return True
    else:
        logger.exception(f"Неизвестная ошибка: {exception}")
        return True


async def safe_send_message(bott: Bot, recipient, text: str, reply_markup=ReplyKeyboardRemove(), retry_attempts=3, delay=5) -> Message:
    """Отправка сообщения с обработкой ClientConnectorError, поддержкой reply_markup и выбором метода отправки."""

    for attempt in range(retry_attempts):
        try:
            if isinstance(recipient, types.Message):
                msg = await recipient.answer(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            elif isinstance(recipient, types.CallbackQuery):
                msg = await recipient.message.answer(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            elif isinstance(recipient, int):
                msg = await bott.send_message(chat_id=recipient, text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            else:
                raise TypeError(f"Неподдерживаемый тип recipient: {type(recipient)}")

            return msg

        except ClientConnectorError as e:
            logger.error(f"Ошибка подключения: {e}. Попытка {attempt + 1} из {retry_attempts}.")
            if attempt < retry_attempts - 1:
                await asyncio.sleep(delay)
            else:
                logger.error(f"Не удалось отправить сообщение после {retry_attempts} попыток.")
                return None
        except Exception as e:
            logger.error(str(e))
            return None


def webscrab_error_handler(func):
    @wraps(func)
    async def wrapper(*args, retry_attempts=3, delay_between_retries=5, **kwargs):
        for attempt in range(retry_attempts):
            try:
                result = await func(*args, **kwargs)
                return result
            except ProxyError as e:
                logger.error(f"Ошибка ожидания загрузки страницы: {e}")
                await safe_send_message(bot, 483458201, "Proxy fallen")  # temporary
                return None
            except TimeoutException as e:
                logger.error(f"Ошибка ожидания загрузки страницы: {e}")
                await safe_send_message(bot, 483458201, 'пезда')
                return None
            except NoSuchElementException as e:
                logger.error(f"Ошибка нахождения элемента для ввода логина/пароля: {e}")
                await safe_send_message(bot, 483458201, 'пезда')
                return None
            except ElementNotInteractableException as e:
                logger.error(f"Элемент не может быть использован: {e}")
                await safe_send_message(bot, 483458201, 'пезда')
                return None
            except WebDriverException as e:
                logger.error(f"Ошибка инициализации драйвера: {e}")
                await safe_send_message(bot, 483458201, 'пезда')
                return None
            except (ClientError, TimeoutError) as e:  # Обработка HTTP ошибок
                logger.error(f"Ошибка HTTP клиента или превышение времени ожидания: {e}")
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(delay_between_retries)
                else:
                    logger.exception(f"{str(e)}. All attempts spent {attempt + 1}/{retry_attempts}")
                    await safe_send_message(bot, 483458201, 'HTTP timeout error occurred')
                    return None
            except Exception as e:
                logger.error(f"Неизвестная ошибка: {str(e)}")
                await safe_send_message(bot, 483458201, 'пезда')
                return None
    return wrapper


def db_error_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Error404 as e:
            logger.exception(str(e))
            return None
        except DatabaseConnectionError as e:
            logger.exception(str(e))
            return None
        except Error409 as e:
            logger.exception(str(e))
            return None
        except Exception as e:
            logger.exception(f"Неизвестная ошибка: {str(e)}")
            return None
    return wrapper


def gpt_error_handler(func):
    @wraps(func)
    async def wrapper(*args, retry_attempts=3, delay_between_retries=5, **kwargs):
        for attempt in range(retry_attempts):
            try:
                return await func(*args, **kwargs)
            except NumberError as e:
                logger.exception(f"Number Error: {e}")
                await safe_send_message(bot, e.user_id, f"Number Error from {e.user_id}, please visit https://www.mamba.ru/chats/{e.dialog_id}/contact")
            except ContentError as e:
                logger.exception(f"{str(e)}. Try {attempt + 1}/{retry_attempts}")
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(delay_between_retries)
                else:
                    logger.exception(f"{str(e)}. All attempts spent {attempt + 1}/{retry_attempts}")
                    return None
            except FileError as e:
                logger.exception(f"File Error: {e}, user with id {e.user_id}")
                await safe_send_message(bot, 483458201, f"File Error from {e.user_id}")  # temporary
                await safe_send_message(bot, e.user_id, f"File Error from {e.user_id}")
            except AuthenticationError as e:
                logger.exception(f"Authentication Error: {e}")
                return None
            except RateLimitError as e:
                logger.exception(f"Rate Limit Exceeded: {e}")
                return None
            except APIConnectionError as e:
                logger.exception(f"API Connection Error: {e}. Try {attempt + 1}/{retry_attempts}")
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(delay_between_retries)
                else:
                    logger.exception(f"API Connection Error: {e}. All attempts spent {attempt + 1}/{retry_attempts}")
                    return None
            except APIError as e:
                logger.exception(f"API Error: {e}")
                return None
            except Exception as e:
                logger.exception(f"Неизвестная ошибка: {str(e)}")
                return None
    return wrapper


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
