from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException


from brains.brain import check_dialog, read_msg, write_msg
from database.req import get_proxy_by_id, get_best_proxy, update_acc, get_dialog
from bot.handlers.errors import webscrab_error_handler
from errors.errors import ProxyError


@webscrab_error_handler
async def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


async def close_popup(driver):
    try:
        close_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@data-name="turn-on-push-notifications-cancel-action"]'))
        )
        close_button.click()
    except:
        pass


async def check_proxy(proxy):
    return True


@webscrab_error_handler
async def proxy_initialization(user_id, proxy_id):
    proxy = await get_proxy_by_id(proxy_id)
    if not check_proxy(proxy):
        new_proxy_id = await get_best_proxy()
        if not new_proxy_id:
            raise ProxyError
        await update_acc(user_id, "mamba", {'proxy_id': new_proxy_id})
        await proxy_initialization(user_id, new_proxy_id)
        return
    chrome_options = Options()
    chrome_options.add_argument(f'--proxy-server={proxy.proxy}')
    return chrome_options


@webscrab_error_handler
async def create_con(options):
    chrome_driver_path = "/Users/timofejsosnin/PycharmProjects/k_bot/k_bot/hands/chromedriver"
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service)  # webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 10)
    return driver, wait


@webscrab_error_handler
async def close_con(driver):
    driver.quit()


async def captcha_close():
    # TODO: implement
    pass


@webscrab_error_handler
async def mamba_login(driver, wait, username, pas):
    driver.get("https://www.mamba.ru/ru/login")
    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
    time.sleep(5)
    login_field = driver.find_element(By.NAME, "login")
    login_field.send_keys(username)
    time.sleep(5)
    password_field = driver.find_element(By.NAME, "password")
    password_field.send_keys(pas)
    time.sleep(5)
    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_button.click()
    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")


@webscrab_error_handler
async def mamba_dialog_handler(driver, wait, dialog, user_id):
    unread_count = int(dialog.find_element(By.XPATH, './/span[@class="sc-d27dsj-0 fujUOM"]').text)
    dialog.click()
    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
    time.sleep(10)
    current_url = driver.current_url
    dialog_id = int(current_url.split('/')[-2])
    if not await check_dialog(dialog_id, user_id):
        return
    dialog_struct = await get_dialog(dialog_id)
    messages = driver.find_elements(By.XPATH, '//span[@data-name="message-text"]')
    messages = messages[-unread_count:]
    msg = ''
    for message in messages:
        if message.text == "Привет! Похоже, что мы понравились друг другу. Давай пообщаемся!":
            continue
        msg += message.text + '\n'
    if not await read_msg(dialog_id, msg):
        return
    flag, ans = await write_msg(dialog_id, msg)
    if not flag:
        return
    for an in ans.split('\n'):
        message_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'textarea[data-name="input-textarea"]'))
        )
        message_input.click()
        message_input.send_keys(an)

        send_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@data-name="messenger-send-message-icon"]'))
        )
        send_button.click()


@webscrab_error_handler
async def mamba_dialogs_handler(driver, wait, user_id):
    while True:
        time.sleep(20)
        await close_popup(driver)
        unread_dialogs = driver.find_elements(By.XPATH, '//a[.//div[@data-name="counter-unread-message"]]')
        # print(f"Количество непрочитанных диалогов: {len(unread_dialogs)}")

        if not unread_dialogs:
            # print("Нет непрочитанных диалогов.")
            break
        dialog = unread_dialogs[0]
        await mamba_dialog_handler(driver, wait, dialog, user_id)


@webscrab_error_handler
async def mamba_dialog_to_data_handler(driver, wait, dialog):
    dialog.click()
    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
    time.sleep(10)
    messages = driver.find_elements(By.XPATH, '//span[@data-name="message-text"]')

    data = {'messages': []}
    for msg in messages:
        if msg.text == "Привет! Похоже, что мы понравились друг другу. Давай пообщаемся!":
            continue
        data['messages'].append(
            {'sender': ("собеседник" if msg.location['x'] < 1000 else "пользователь"), 'text': msg.text})

    return data


@webscrab_error_handler
async def mamba_dialogs_to_data_handler(driver, wait):
    # TODO: need optimize func and make better
    parsed_hrefs = []
    data = []

    while True:
        try:
            await scroll_to_bottom(driver)
            await close_popup(driver)

            all_dialogs = driver.find_elements(By.XPATH,
                                               '//a[contains(@class, "sc-qyouz1-0") and contains(@class, "sc-1psbcvc-0") and contains(@class, "bcCKMU") and contains(@class, "eRGrrJ")]')
            unread_dialogs = driver.find_elements(By.XPATH, '//a[.//div[@data-name="counter-unread-message"]]')

            all_hrefs = {d.get_attribute('href') for d in all_dialogs}
            unread_hrefs = {d.get_attribute('href') for d in unread_dialogs}
            read_hrefs = list(all_hrefs - unread_hrefs - set(parsed_hrefs))

            if not read_hrefs:
                print("Нет новых прочитанных диалогов.")
                break

            read_dialogs = [
                dialog for dialog in all_dialogs
                if dialog.get_attribute('href') in read_hrefs
            ]

            cur_data = await mamba_dialog_to_data_handler(driver, wait, read_dialogs[0])
            parsed_hrefs.append(read_dialogs[0].get_attribute('href'))
            data.append(cur_data)
        except StaleElementReferenceException:
            print("Обнаружено StaleElementReferenceException. Перезагрузка страницы...")
            driver.refresh()
            time.sleep(20)

    return data
