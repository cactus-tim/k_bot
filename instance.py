from aiogram import Bot
from aiogram.enums import ParseMode
import os
from dotenv import load_dotenv
from openai import OpenAI
import sys
from aiogram.client.bot import DefaultBotProperties
import logging
import asyncio

sys.path.append(os.path.join(sys.path[0], 'k_bot'))

load_dotenv('.env')
token = os.getenv('TOKEN_API_TG')
SQL_URL_RC = (f'postgresql+asyncpg://{os.getenv("DB_USER")}:{os.getenv("DB_PASS")}'
              f'@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}')

bot = Bot(
    token=token,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )


logger = logging.getLogger(__name__)

event = asyncio.Event()

# token = os.getenv('TOKEN_API_GPT')
# client = OpenAI(api_key=token)