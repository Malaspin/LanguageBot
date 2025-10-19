from pydantic.v1 import BaseSettings 
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from urllib.parse import quote

class ConfigBase(BaseSettings):
    class Config:
        env_file = '.env'

class DBSettings(ConfigBase):
    DB_HOST : str 
    DB_PORT : str 
    DB_NAME : str 
    DB_USER : str 
    DB_PASS : str 

settings_db = DBSettings()

DATABASE_ASYNC_URL = (
    f'postgresql+asyncpg://{settings_db.DB_USER}:{quote(settings_db.DB_PASS)}@{settings_db.DB_HOST}:{settings_db.DB_PORT}/{settings_db.DB_NAME}'

)

DATABASE_SYNC_URL = (
    f'postgresql+psycopg2://{settings_db.DB_USER}:{quote(settings_db.DB_PASS)}@{settings_db.DB_HOST}:{settings_db.DB_PORT}/{settings_db.DB_NAME}'

)

sync_engine = create_engine(DATABASE_SYNC_URL)
async_engine = create_async_engine(DATABASE_ASYNC_URL)

class BotSettings(ConfigBase):
    BOT_TOKEN: str

settings_bot = BotSettings()