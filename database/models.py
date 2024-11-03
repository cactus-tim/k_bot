from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, ARRAY, BigInteger, ForeignKey, Numeric, JSON, Date
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs

from bot_instance import SQL_URL_RC

engine = create_async_engine(url=SQL_URL_RC, echo=True)
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id = Column(BigInteger, primary_key=True, index=True, nullable=False)
    info = Column(String, default='')
    f_a_id = Column(String, default='')
    s_a_id = Column(String, default='')
    thread = Column(String, default='')
    services = Column(ARRAY(String), default=list)
    cur_service = Column(String, default='')
    questing = Column(Boolean, default=False)
    # is_quested = Column(Boolean, default=False)
    # is_active = Column(Boolean, default=False)
    # is_superuser = Column(Boolean, default=False)


class SecondPerson(Base):
    __tablename__ = "second_person"

    id = Column(BigInteger, primary_key=True, index=True, nullable=False)  # autoincrement=True
    info = Column(String, default='')
    status = Column(String, default='')  # TODO: start state


class Dialogs(Base):
    __tablename__ = "dialogs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)
    second_person_id = Column(BigInteger, ForeignKey("second_person.id"), nullable=False)
    thread_f_a = Column(String, default='')
    thread_s_a = Column(String, default='')
    status = Column(String, default='')  # TODO: start state


class Proxy(Base):
    __tablename__ = "proxy"

    id = Column(Integer, primary_key=True)
    proxy = Column(String, default='', nullable=False)
    in_use = Column(Integer, default=0)
    all_use = Column(Integer, default=0)
    is_life = Column(Boolean, default=True)


class Accs(Base):
    __tablename__ = "accs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)
    proxy_id = Column(Integer, ForeignKey("proxy.id"), nullable=False)
    service = Column(String, default='', nullable=False)
    login = Column(String, default='')
    password = Column(String, default='')


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
