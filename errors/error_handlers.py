from functools import wraps
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException, ElementNotInteractableException

from bot_instance import logger


def webscrab_error_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        nonlocal_driver = None
        try:
            return await func(*args, **kwargs, driver_container=nonlocal_driver)
        except TimeoutException as e:
            logger.error(f"Ошибка ожидания загрузки страницы: {e}")
        except NoSuchElementException as e:
            logger.error(f"Ошибка нахождения элемента для ввода логина/пароля: {e}")
        except ElementNotInteractableException as e:
            logger.error(f"Элемент не может быть использован: {e}")
        except WebDriverException as e:
            logger.error(f"Ошибка инициализации драйвера: {e}")
        except Exception as e:
            logger.error(f"Неизвестная ошибка: {str(e)}")
        finally:
            if nonlocal_driver is not None:
                try:
                    nonlocal_driver.quit()
                except WebDriverException as e:
                    logger.exception(f"Ошибка при закрытии драйвера: {e}")
            return None
    return wrapper
