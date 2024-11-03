from sqlalchemy import select, desc, distinct, and_

from database.models import User, SecondPerson, Dialogs, Proxy, Accs, async_session


async def get_user(tg_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.id == tg_id))
        if user:
            return user
        else:
            return "not created"


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


async def get_all_users_ids():
    async with async_session() as session:
        users_tg_id = await session.execute(select(distinct(User.id)))
        users_tg_ids = users_tg_id.scalars().all()
        if not users_tg_ids:
            raise Error404
        return users_tg_ids


async def get_s_p(id: int):
    async with async_session() as session:
        s_p = await session.scalar(select(SecondPerson).where(SecondPerson.id == id))
        if s_p:
            return s_p
        else:
            return "not created"


async def create_s_p(data:dict):
    async with async_session() as session:
        s_p_data = SecondPerson(**data)
        session.add(s_p_data)
        await session.commit()


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


async def get_proxy(id: int):
    async with async_session() as session:
        proxy = await session.scalar(select(Proxy).where(Proxy.id == id))
        if proxy:
            return proxy
        else:
            return "not created"


async def create_proxy(id: int, proxy_d: str):
    async with async_session() as session:
        proxy = await get_proxy(id)
        data = {}
        if proxy == 'not created':
            data['id'] = id
            data['proxy'] = proxy_d
            proxy_data = Proxy(**data)
            session.add(proxy_data)
            await session.commit()
        else:
            raise Error409


async def update_proxy(id: int, data: dict):
    async with async_session() as session:
        proxy = await get_proxy(id)
        if proxy == 'not created':
            raise Error404
        else:
            for key, value in data.items():
                setattr(proxy, key, value)
            session.add(proxy)
            await session.commit()


async def get_best_proxy():
    pass


async def get_acc():
    pass


async def get_acc_by_service():
    pass


async def create_acc(tg_id: int, service: str):  # TODO: automatically add proxy (and implement proxy_check)
    pass


async def update_acc(tg_id: int, service: str, data: dict):
    pass


async def get_dialog():
    pass


async def create_dialog():
    pass


async def update_dialog():
    pass

