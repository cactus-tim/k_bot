from sqlalchemy import select, desc, distinct, and_

from database.models import User, Dialogs, Proxy, Accs, async_session
from errors.errors import Error404, Error409, ContentError
from instance import client
from bot.handlers.errors import gpt_error_handler, db_error_handler


@gpt_error_handler
async def create_thread():
    thread = client.beta.threads.create()
    return thread.id


@gpt_error_handler
async def initialize_dialog(assistant_id, thread_id, mes):
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


@db_error_handler
async def get_user(tg_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.id == tg_id))
        if user:
            return user
        else:
            return "not created"


@db_error_handler
async def create_user(tg_id: int):
    async with async_session() as session:
        user = await get_user(tg_id)
        data = {}
        if user == 'not created':
            data['id'] = tg_id
            user_data = User(**data)
            session.add(user_data)
            await session.commit()
        else:
            raise Error409


@db_error_handler
async def update_user(tg_id: int, data: dict):
    async with async_session() as session:
        user = await get_user(tg_id)
        if user == 'not created':
            raise Error404
        else:
            for key, value in data.items():
                setattr(user, key, value)
            session.add(user)
            await session.commit()


@db_error_handler
async def get_all_users_ids():
    async with async_session() as session:
        users_tg_id = await session.execute(select(distinct(User.id)))
        users_tg_ids = users_tg_id.scalars().all()
        if not users_tg_ids:
            raise Error404
        return users_tg_ids


@db_error_handler
async def get_proxy_by_host(proxy: str):
    async with async_session() as session:
        proxyy = await session.scalar(select(Proxy).where(Proxy.host == proxy))
        if proxyy:
            return proxyy
        else:
            return "not created"


@db_error_handler
async def create_proxy(proxy_row: str):
    async with async_session() as session:
        proxy_row_list = proxy_row.split(':')
        proxy = await get_proxy_by_host(f"{proxy_row_list[0]}:{proxy_row_list[1]}")
        data = {}
        if proxy == 'not created':
            proxy_row_list = proxy_row.split(':')
            data['host'] = f"{proxy_row_list[0]}:{proxy_row_list[1]}"
            data['login'] = proxy_row_list[2]
            data['password'] = proxy_row_list[3]
            proxy_data = Proxy(**data)
            session.add(proxy_data)
            await session.commit()
        else:
            raise Error409


@db_error_handler
async def update_proxy(proxy_row: str, data: dict):
    async with async_session() as session:
        proxy_row_list = proxy_row.split(':')
        proxy = await get_proxy_by_host(f"{proxy_row_list[0]}:{proxy_row_list[1]}")
        if proxy == 'not created':
            raise Error404
        else:
            for key, value in data.items():
                setattr(proxy, key, value)
            session.add(proxy)
            await session.commit()


@db_error_handler
async def get_proxy_by_id(proxy_id: int):
    async with async_session() as session:
        proxyy = await session.scalar(select(Proxy).where(Proxy.id == proxy_id))
        if proxyy:
            return proxyy
        else:
            return "not created"


@db_error_handler
async def get_proxy_id_by_proxy(proxy: str):
    async with async_session() as session:
        proxyy = await session.scalar(select(Proxy).where(Proxy.host == proxy))
        if proxyy:
            return proxyy.id
        else:
            return "not created"


@db_error_handler
async def get_best_proxy():
    async with async_session() as session:
        best_proxy = await session.scalar(select(Proxy).order_by(Proxy.in_use))
        if best_proxy:
            return best_proxy.id
        else:
            return None


@db_error_handler
async def del_proxy(proxy_row: str):
    async with async_session() as session:
        proxy_row_list = proxy_row.split(':')
        proxy = await get_proxy_by_host(f"{proxy_row_list[0]}:{proxy_row_list[1]}")
        if proxy == "not created":
            raise Error409
        else:
            await session.delete(proxy)
            await session.commit()
            return "ok"


@db_error_handler
async def get_acc(tg_id: int, service: str):
    async with async_session() as session:
        acc = await session.scalar(select(Accs).where(and_(
            Accs.user_id == tg_id,
            Accs.service == service
        )))
        if acc:
            return acc
        else:
            return "not created"


@db_error_handler
async def create_acc(tg_id: int, service: str):
    async with async_session() as session:
        acc = await get_acc(tg_id, service)
        data = {}
        if acc == 'not created':
            data['user_id'] = tg_id
            data['proxy_id'] = await get_best_proxy()
            data['service'] = service
            user_data = Accs(**data)
            session.add(user_data)
            await session.commit()
        else:
            raise Error409


@db_error_handler
async def update_acc(tg_id: int, service: str, data: dict):
    async with async_session() as session:
        acc = await get_acc(tg_id, service)
        if acc == 'not created':
            raise Error404
        else:
            for key, value in data.items():
                setattr(acc, key, value)
            session.add(acc)
            await session.commit()


@db_error_handler
async def del_acc(tg_id: int, service: str):
    async with async_session() as session:
        acc = await get_acc(tg_id, service)
        if acc == "not created":
            raise Error409
        else:
            await session.delete(acc)
            await session.commit()
            return "ok"


@db_error_handler
async def get_all_accs():
    async with async_session() as session:
        accs = await session.execute(select(Accs))
        acc_tg_ids = accs.scalars().all()
        if not acc_tg_ids:
            raise Error404
        return acc_tg_ids


@db_error_handler
async def get_dialog(dialog_id: int):
    async with async_session() as session:
        dialog = await session.scalar(select(Dialogs).where(Dialogs.id == dialog_id))
        if dialog:
            return dialog
        else:
            return "not created"


@db_error_handler
async def create_dialog(dialog_id: int, user_id: int):
    async with async_session() as session:
        dialog = await get_dialog(dialog_id)
        user = await get_user(user_id)
        data = {}
        if dialog == 'not created':
            data['id'] = dialog_id
            data['user_id'] = user_id
            data['thread_brain'] = await create_thread()
            data['thread_def'] = await create_thread()
            await initialize_dialog(user.def_id, data['thread_def'], "Давай начнем оценивать сообщения")
            dialog_data = Dialogs(**data)
            session.add(dialog_data)
            await session.commit()
        else:
            raise Error409


@db_error_handler
async def update_dialog(dialog_id: int, data: dict):
    async with async_session() as session:
        dialog = await get_dialog(dialog_id)
        if dialog == 'not created':
            raise Error404
        else:
            for key, value in data.items():
                setattr(dialog, key, value)
            session.add(dialog)
            await session.commit()


async def get_upd():
    pass


async def create_upd():
    pass


async def del_upd():
    pass


async def get_upd_wait():
    pass


async def create_upd_wait():
    pass


async def del_upd_wait():
    pass
