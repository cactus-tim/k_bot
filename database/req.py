from sqlalchemy import select, desc, distinct, and_

from database.models import User, SecondPerson, Dialogs, Proxy, Accs, async_session
from errors.errors import Error404, Error409
from instance import client
from errors.error_handlers import db_error_handler


async def create_thread():
    thread = client.beta.threads.create()
    return thread.id


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
async def get_s_p(id: int):
    async with async_session() as session:
        s_p = await session.scalar(select(SecondPerson).where(SecondPerson.id == id))
        if s_p:
            return s_p
        else:
            return "not created"


@db_error_handler
async def create_s_p(data:dict):
    async with async_session() as session:
        s_p_data = SecondPerson(**data)
        session.add(s_p_data)
        await session.commit()


@db_error_handler
async def update_s_p(id: int, data: dict):
    async with async_session() as session:
        s_p = await get_s_p(id)
        if s_p == 'not created':
            raise Error404
        else:
            for key, value in data.items():
                setattr(s_p, key, value)
            session.add(s_p)
            await session.commit()


@db_error_handler
async def get_proxy_by_proxy(proxy: str):
    async with async_session() as session:
        proxyy = await session.scalar(select(Proxy).where(Proxy.proxy == proxy))
        if proxyy:
            return proxyy
        else:
            return "not created"


@db_error_handler
async def create_proxy(proxy_d: str):
    async with async_session() as session:
        proxy = await get_proxy_by_proxy(proxy_d)
        data = {}
        if proxy == 'not created':
            data['proxy'] = proxy_d
            proxy_data = Proxy(**data)
            session.add(proxy_data)
            await session.commit()
        else:
            raise Error409


@db_error_handler
async def update_proxy(proxy_d: str, data: dict):
    async with async_session() as session:
        proxy = await get_proxy_by_proxy(proxy_d)
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
        proxyy = await session.scalar(select(Proxy).where(Proxy.proxy == proxy))
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
async def del_proxy(proxy_d: str):
    async with async_session() as session:
        proxy = await get_proxy_by_proxy(proxy_d)
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
        data = {}
        if dialog == 'not created':
            data['user_id'] = user_id
            data['thread_brain'] = await create_thread()
            # TODO: initialize dialog
            data['thread_def'] = await create_thread()
            # TODO: initialize dialog
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
