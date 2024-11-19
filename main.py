import asyncio
import time
from random import randint

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from confige import BotConfig
from pytz import timezone

from database.req import get_all_accs, get_user
from hands.hand import mamba_hand
from instance import bot, scheduler
from bot.handlers import user, errors, questionary, admin, def_update
from database.models import async_main


def register_routers(dp: Dispatcher) -> None:
    dp.include_routers(user.router, errors.router, questionary.router, admin.router, def_update.router)


async def loop():
    # time.sleep(randint(0, 52431))
    accs = await get_all_accs()
    for acc in accs:
        user = await get_user(acc.user_id)
        if user.is_active:
            await mamba_hand(acc.user_id)


async def main() -> None:
    await async_main()

    config = BotConfig(
        admin_ids=[],
        welcome_message=""
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp["config"] = config

    register_routers(dp)

    scheduler.add_job(loop, 'cron', hour=10, minute=3, id='loop', timezone=timezone('Europe/Moscow'))
    scheduler.add_job(loop, 'cron', hour=14, minute=7, id='loop', timezone=timezone('Europe/Moscow'))
    scheduler.add_job(loop, 'cron', hour=19, minute=5, id='loop', timezone=timezone('Europe/Moscow'))
    scheduler.add_job(loop, 'cron', hour=23, minute=11, id='loop', timezone=timezone('Europe/Moscow'))

    try:
        await loop()
        # scheduler.start()
        await dp.start_polling(bot, skip_updates=True)
    except Exception as _ex:
        print(f'Exception: {_ex}')


if __name__ == '__main__':
    asyncio.run(main())
