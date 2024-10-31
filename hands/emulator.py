from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
import time
from webdriver_manager.chrome import ChromeDriverManager


def close_popup():
    try:
        close_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@data-name="turn-on-push-notifications-cancel-action"]'))
        )
        close_button.click()
        print("Плашка закрыта")
    except:
        pass


# Initialize Chrome driver
chrome_driver_path = "/Users/timofejsosnin/PycharmProjects/k_bot/k_bot/hands/chromedriver"
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service)

# Открываем сайт
driver.get("https://www.mamba.ru/ru/login")
wait = WebDriverWait(driver, 10)
wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")

# Вводим логин и пароль
login_field = driver.find_element(By.NAME, "login")
login_field.send_keys("lida.aiseller@gmail.com")
time.sleep(5)
password_field = driver.find_element(By.NAME, "password")
password_field.send_keys("T37RrMDT")
time.sleep(5)
submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
submit_button.click()
wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")

while True:
    time.sleep(20)
    close_popup()
    # Обновляем список диалогов с непрочитанными сообщениями
    unread_dialogs = driver.find_elements(By.XPATH, '//a[.//div[@data-name="counter-unread-message"]]')
    print(f"Количество непрочитанных диалогов: {len(unread_dialogs)}")

    if not unread_dialogs:
        print("Нет непрочитанных диалогов.")
        break

    dialog = unread_dialogs[0]
    try:
        # Клик по диалогу
        dialog.click()
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        time.sleep(10)
        # Собираем сообщения
        messages = driver.find_elements(By.XPATH, '//span[@data-name="message-text"]')
        msg = ''
        for message in messages:
            # TODO: need only last n messages (you know how many unread messages are, but where is it&)
            if message.text == "Привет! Похоже, что мы понравились друг другу. Давай пообщаемся!":
                continue
            msg += message.text + '\n'
        print(msg)  # TODO: implement handler
        time.sleep(15)
        # Ответ на сообщение
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

        # unread_dialogs.pop(-1)

        # Переход обратно к списку диалогов
        # driver.back()
        # wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")

    except Exception as e:
        print(f"Error processing dialog: {e}")
        driver.back()
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        continue

driver.quit()
