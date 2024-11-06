from functools import wraps
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException, ElementNotInteractableException

from instance import logger


def webscrab_error_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            return result
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
