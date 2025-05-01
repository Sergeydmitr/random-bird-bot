import logging

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from src.models import Subscriber
from src.settings import settings

logger = logging.getLogger(__name__)


async def init_db() -> None:
    client = AsyncIOMotorClient(settings.mongo_uri)
    await init_beanie(
        database=client[settings.mongo_db_name], document_models=[Subscriber]
    )
    logger.info("Подключение к базе данных MongoDB установлено.")


async def add_subscriber(chat_id: int) -> bool:
    existing_subscriber = await Subscriber.find_one(Subscriber.chat_id == chat_id)
    if existing_subscriber:
        return False  # Подписчик уже существует
    subscriber = Subscriber(chat_id=chat_id)
    await subscriber.insert()
    logger.info(f"Новый подписчик добавлен: {chat_id}")
    return True


async def remove_subscriber(chat_id: int) -> None:
    await Subscriber.find_one(Subscriber.chat_id == chat_id).delete()
    logger.info(f"Подписчик удален: {chat_id}")


async def get_all_subscribers() -> list[Subscriber]:
    return await Subscriber.find_all().to_list()
