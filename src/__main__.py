import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.utils import get_random_bird_image
from src.settings import settings
from src.db import add_subscriber, get_all_subscribers, remove_subscriber, init_db


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", stream=sys.stdout)
logger = logging.getLogger(__name__)

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    is_new = await add_subscriber(message.chat.id)
    if is_new:
        await message.reply("Вы подписались на ежедневные фотографии птиц!")
    else:
        await message.reply("Вы уже подписаны на ежедневные фотографии птиц.")


async def send_daily_bird_photos(bot: Bot) -> None:
    """Ежедневная рассылка фотографий птиц."""
    subscribers = await get_all_subscribers()
    if not subscribers:
        logger.info("Нет подписчиков для рассылки.")
        return

    for subscriber in subscribers:
        image_url = await get_random_bird_image(subscriber.bird_type)
        if not image_url:
            logger.error("Не удалось получить изображение птицы.")
            continue

        try:
            await bot.send_photo(
                chat_id=subscriber.chat_id,
                photo=image_url,
                caption=f"Ежедневная фотография овсянки",
            )
            logger.info(f"Фото отправлено в чат {subscriber.chat_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в чат {subscriber.chat_id}: {e}")
            # Удаляем подписчика, если отправка не удалась (например, пользователь заблокировал бота)
            if "blocked" in str(e).lower():
                await remove_subscriber(subscriber.chat_id)


async def main() -> None:
    await init_db()

    bot = Bot(token=settings.api_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_bird_photos, "cron", hour=13, args=[bot])  # Рассылка в 9 утра
    scheduler.start()
    logger.info("Планировщик запущен.")

    try:
        logger.info("Бот запущен. Ожидание сообщений...")
        await dp.start_polling(bot)
    finally:
        try:
            scheduler.shutdown(wait=False)
            logger.info("Планировщик остановлен.")
        except Exception as e:
            logger.warning(f"Ошибка при остановке планировщика: {e}")
        await bot.session.close()
        logger.info("Сессия бота завершена.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен вручную.")