import asyncio
import time
from random import randint

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers.errors import safe_send_message
from confige import BotConfig
from aiogram.types import Message
from aiogram.filters import Command
from pytz import timezone

from database.req import get_all_accs, get_user
from hands.hand import mamba_hand
from instance import bot, scheduler, logger
from bot.handlers import user, errors, questionary, admin, def_update
from database.models import async_main


@admin.router.message(Command('now'))
async def now_run(message: Message):
    user = await get_user(message.from_user.id)
    if not user.is_superuser:
        return
    await safe_send_message(bot, user.id, 'поехали')
    await loop()


def register_routers(dp: Dispatcher) -> None:
    dp.include_routers(user.router, errors.router, questionary.router, admin.router, def_update.router)


async def loop():
    time.sleep(randint(0, 52431))
    accs = await get_all_accs()
    if not accs:
        return
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

    scheduler.add_job(loop, 'cron', hour=10, minute=3, id='loop1')
    scheduler.add_job(loop, 'cron', hour=14, minute=7, id='loop2')
    scheduler.add_job(loop, 'cron', hour=19, minute=5, id='loop3')
    scheduler.add_job(loop, 'cron', hour=23, minute=11, id='loop4')

    scheduler.start()

    try:
        # await asyncio.gather(
        #     dp.start_polling(bot, skip_updates=True),
        #     loop()
        # )
        await dp.start_polling(bot, skip_updates=True)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Остановка бота по сигналу")
    except Exception as _ex:
        await safe_send_message(bot, 483458201, "Классически упали(")
        logger.exception(f'Exception: {_ex}')
    finally:
        await bot.close()
        scheduler.shutdown()
        logger.info("Scheduler остановлен и бот закрыт")


if __name__ == '__main__':
    asyncio.run(main())
