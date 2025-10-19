from database.create_db_table import create_table
from handlers.bot_handler import bot_hendler_start
from services.db.db_service import DataBaseAPI
import asyncio

db_api = DataBaseAPI()

async def main():
    create_table()
    data = await db_api.read_json()
    await db_api.add_data(data=data)
    await bot_hendler_start()

if __name__ == '__main__':
    asyncio.run(main())