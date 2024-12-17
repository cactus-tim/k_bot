import contextlib
import tempfile
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import zipfile
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException


from brains.brain import check_dialog, read_msg, write_msg
from database.req import get_proxy_by_id, get_best_proxy, update_acc, get_dialog
from bot.handlers.errors import webscrab_error_handler, safe_send_message
from errors.errors import ProxyError
from instance import bot


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
    if not await check_proxy(proxy):
        new_proxy_id = await get_best_proxy()
        if not new_proxy_id:
            raise ProxyError
        await update_acc(user_id, "mamba", {'proxy_id': new_proxy_id})
        proxy = await proxy_initialization(user_id, new_proxy_id)
        return proxy
    return proxy


class ChromeExtended(webdriver.Chrome):
    def __init__(self, *args, options=None, proxy=None, **kwargs):
        options = options or Options()

        # options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        if proxy:
            context = tempfile.TemporaryDirectory()
        else:
            context = contextlib.nullcontext()

        with context as extensionDirpath:
            self._setupProxy(extensionDirpath, proxy, options)

            service = Service('/Users/timofejsosnin/.wdm/drivers/chromedriver/mac64/131.0.6778.85/chromedriver-mac-arm64/chromedriver')
            super().__init__(*args, options=options, service=service, **kwargs)

    def _setupProxy(self, extensionDirpath, proxy, options):
        if not proxy:
            return

        parsedProxy = urlparse(proxy)

        manifest_json = '{"version":"1.0.0","manifest_version":2,"name":"Chrome Proxy","permissions":["proxy","tabs","unlimitedStorage","storage","<all_urls>","webRequest","webRequestBlocking"],"background":{"scripts":["background.js"]},"minimum_chrome_version":"22.0.0"}'
        background_js = 'var e={mode:"fixed_servers",rules:{singleProxy:{scheme:"%s",host:"%s",port:parseInt(%s)},bypassList:["localhost"]}};chrome.proxy.settings.set({value:e,scope:"regular"},(function(){})),chrome.webRequest.onAuthRequired.addListener((function(e){return{authCredentials:{username:"%s",password:"%s"}}}),{urls:["<all_urls>"]},["blocking"]);' \
            % (parsedProxy.scheme, parsedProxy.hostname, parsedProxy.port, parsedProxy.username, parsedProxy.password)

        with open(f"{extensionDirpath}/manifest.json", "w", encoding="utf8") as f:
            f.write(manifest_json)
        with open(f"{extensionDirpath}/background.js", "w", encoding="utf8") as f:
            f.write(background_js)

        options.add_argument(f"--load-extension={extensionDirpath}")


@webscrab_error_handler
async def create_con(proxy=None):
    driver = ChromeExtended(proxy=proxy)
    driver.implicitly_wait(10)  # TODO: delete after tests
    wait = WebDriverWait(driver, 30)
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
    time.sleep(20)
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
        await safe_send_message(bot, 483458201, 'все круто!')


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
