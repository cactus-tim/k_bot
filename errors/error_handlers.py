from functools import wraps
import asyncio
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException, ElementNotInteractableException
from openai import AuthenticationError, RateLimitError, APIConnectionError, APIError

from bot.handlers.errors import safe_send_message
from instance import logger, bot
from errors import *


def webscrab_error_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            return result
        except ProxyError as e:
            logger.error(f"Ошибка ожидания загрузки страницы: {e}")
            await safe_send_message(bot, 483458201, "Proxy fallen")  # temporary
            return None
        except TimeoutException as e:
            logger.error(f"Ошибка ожидания загрузки страницы: {e}")
            return None
        except NoSuchElementException as e:
            logger.error(f"Ошибка нахождения элемента для ввода логина/пароля: {e}")
            return None
        except ElementNotInteractableException as e:
            logger.error(f"Элемент не может быть использован: {e}")
            return None
        except WebDriverException as e:
            logger.error(f"Ошибка инициализации драйвера: {e}")
            return None
        except Exception as e:
            logger.error(f"Неизвестная ошибка: {str(e)}")
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
