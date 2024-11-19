from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, ARRAY, BigInteger, ForeignKey, Numeric, JSON, Date
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs

from instance import SQL_URL_RC

engine = create_async_engine(url=SQL_URL_RC, echo=True)
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id = Column(BigInteger, primary_key=True, index=True, nullable=False)
    name = Column(String, default='')
    info = Column(String, default='')
    brain_id = Column(String, default='')
    def_id = Column(String, default='')
    thread_q1 = Column(String, default='')
    thread_q2 = Column(String, default='')
    services = Column(ARRAY(String), default=list)
    cur_service = Column(String, default='')
    is_quested1 = Column(Boolean, default=False)
    is_quested2 = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)


class Dialogs(Base):
    __tablename__ = "dialogs"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)
    thread_brain = Column(String, default='')
    thread_def = Column(String, default='')
    status = Column(String, default='in_p')  # in_p, banned, approved


class Proxy(Base):
    __tablename__ = "proxy"

    id = Column(Integer, primary_key=True, autoincrement=True)
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
