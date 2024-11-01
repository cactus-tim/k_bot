from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
import time
from webdriver_manager.chrome import ChromeDriverManager

from errors.error_handlers import webscrab_error_handler


def close_popup(driver):
    try:
        close_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@data-name="turn-on-push-notifications-cancel-action"]'))
        )
        close_button.click()
        print("Плашка закрыта")
    except:
        pass


@webscrab_error_handler
def create_con():
    chrome_driver_path = "/Users/timofejsosnin/PycharmProjects/k_bot/k_bot/hands/chromedriver"
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service)
    wait = WebDriverWait(driver, 10)
    return driver, wait


@webscrab_error_handler
def close_con(driver):
    driver.quit()


@webscrab_error_handler
def mamba_login(driver, wait, username, pas):
    username = "lida.aiseller@gmail.com"
    pas = "T37RrMDT"
    driver.get("https://www.mamba.ru/ru/login")
    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")

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
def mamba_dialog_handler(driver, wait, dialog):
    unread_count = int(dialog.find_element(By.XPATH, './/span[@class="sc-d27dsj-0 fujUOM"]').text)
    dialog.click()
    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
    time.sleep(10)
    messages = driver.find_elements(By.XPATH, '//span[@data-name="message-text"]')
    messages = messages[-unread_count:]
    msg = ''
    for message in messages:
        if message.text == "Привет! Похоже, что мы понравились друг другу. Давай пообщаемся!":
            continue
        msg += message.text + '\n'
    print(msg)  # TODO: implement handler
    time.sleep(15)
    ans = "как дела?"  # TODO: implement handler
    message_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'textarea[data-name="input-textarea"]'))
    )
    message_input.click()
    message_input.send_keys(ans)

    send_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//div[@data-name="messenger-send-message-icon"]'))
    )
    send_button.click()


@webscrab_error_handler
def mamba_dialogs_handler(driver, wait):
    while True:
        time.sleep(20)
        close_popup(driver)
        unread_dialogs = driver.find_elements(By.XPATH, '//a[.//div[@data-name="counter-unread-message"]]')
        print(f"Количество непрочитанных диалогов: {len(unread_dialogs)}")

        if not unread_dialogs:
            print("Нет непрочитанных диалогов.")
            break

        dialog = unread_dialogs[0]
        mamba_dialog_handler(driver, wait, dialog)
