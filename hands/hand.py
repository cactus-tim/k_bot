import asyncio

from database.req import get_acc
from hands.mamba_handlers import create_con, close_con, mamba_login, mamba_dialogs_handler, proxy_initialization, \
    mamba_dialogs_to_data_handler


async def mamba_hand(user_id: int):
    acc = await get_acc(user_id, "mamba")
    options = ''  # await proxy_initialization(acc.proxy_id)

    driver, wait = await create_con(options)

    login = acc.login
    password = acc.password
    await mamba_login(driver, wait, login, password)

    await mamba_dialogs_handler(driver, wait, user_id)

    await close_con(driver)


async def mamba_parsing_dialogs(user_id: int):
    options = ''  # await proxy_initialization(acc.proxy_id)

    driver, wait = await create_con(options)

    login = "lida.aiseller@gmail.com"  # acc.login
    password = "T37RrMDT"  # acc.password
    await mamba_login(driver, wait, login, password)

    dialogs = await mamba_dialogs_to_data_handler(driver, wait)

    await close_con(driver)
    return str(dialogs)

