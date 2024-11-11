import asyncio

from mamba_handlers import create_con, close_con, mamba_login, mamba_dialogs_handler, proxy_initialization, \
    mamba_dialogs_to_data_handler


async def mamba_hand(user_id: int):
    # options = await proxy_initialization(user_id)
    options = ''

    driver, wait = await create_con(options)

    # user = await get_acc(user_id, "mamba")  # TODO: here you need take login pass for user and service
    login = "lida.aiseller@gmail.com"
    password = "T37RrMDT"
    await mamba_login(driver, wait, login, password)

    await mamba_dialogs_handler(driver, wait)

    await close_con()


async def mamba_parsing_dialogs(user_id: int):
    # options = await proxy_initialization(user_id)
    options = ''

    driver, wait = await create_con(options)

    # user = await get_acc(user_id, "mamba")  # TODO: here you need take login pass for user and service
    login = "lida.aiseller@gmail.com"
    password = "T37RrMDT"
    await mamba_login(driver, wait, login, password)

    dialogs = await mamba_dialogs_to_data_handler(driver, wait)

    await close_con()
    return dialogs

