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
    is_quested = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)


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

    user = relationship("User", back_populates="second_person")
    company = relationship("Dialogs", back_populates="user")


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
