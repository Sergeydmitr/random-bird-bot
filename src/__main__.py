import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.db import (
    add_subscriber,
    get_all_subscribers,
    get_bird_type_for_chat,
    init_db,
    remove_subscriber,
    set_bird_type_for_chat,
)
from src.settings import settings
from src.utils import get_random_bird_image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    is_new = await add_subscriber(message.chat.id)
    if is_new:
        await message.reply("Вы подписались на ежедневные фотографии птиц!")
        logger.info(f"Новый подписчик: {message.chat.id}")
    else:
        await message.reply("Вы уже подписаны на ежедневные фотографии птиц.")
        logger.info(f"Подписчик {message.chat.id} уже существует.")


@dp.message(Command("send_now"))
async def command_send_now(message: Message) -> None:
    args = message.text.split(maxsplit=1)

    if len(args) > 1:
        bird_type = args[1].strip()
    else:
        bird_type = await get_bird_type_for_chat(message.chat.id)

    if not bird_type:
        await message.reply(
            "Тип птицы не установлен. Используйте /set_bird_type для установки."
        )
        return

    image_url = await get_random_bird_image(bird_type)
    if not image_url:
        logger.error(f"Не удалось получить изображение для типа птицы: {bird_type}.")
        await message.reply(
            f"К сожалению, не удалось получить изображение для типа птицы: {bird_type}."
        )
        return

    try:
        await message.reply_photo(
            photo=image_url,
            caption=f"Фотография птицы: {bird_type}",
        )
        logger.info(f"Фото отправлено в чат {message.chat.id}")
    except TelegramForbiddenError as e:
        logger.error(f"Ошибка при отправке сообщения в чат {message.chat.id}: {e}")


@dp.message(Command("unsubscribe"))
async def command_unsubscribe(message: Message) -> None:
    await remove_subscriber(message.chat.id)
    await message.reply("Вы отписались от ежедневной рассылки фотографий птиц.")
    logger.info(f"Подписчик {message.chat.id} отписался.")


@dp.message(Command("set_bird_type"))
async def command_set_bird_type(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(
            "Пожалуйста, укажите тип птицы. Пример: /set_bird_type Yellowhammer"
        )
        return

    bird_type = args[1].strip()
    await set_bird_type_for_chat(message.chat.id, bird_type)
    await message.reply(f"Тип птицы для этого чата установлен: {bird_type}")
    logger.info(f"Тип птицы для чата {message.chat.id} установлен: {bird_type}")


async def send_daily_bird_photos(bot: Bot) -> None:
    subscribers = await get_all_subscribers()
    if not subscribers:
        logger.info("Нет подписчиков для рассылки.")
        return

    for subscriber in subscribers:
        image_url = await get_random_bird_image(subscriber.bird_type)
        if not image_url:
            logger.error(
                f"Не удалось получить изображение для подписчика {subscriber.chat_id}."
            )
            continue

        try:
            await bot.send_photo(
                chat_id=subscriber.chat_id,
                photo=image_url,
                caption=f"Ежедневная фотография птицы: {subscriber.bird_type}",
            )
            logger.info(f"Фото отправлено в чат {subscriber.chat_id}")
        except TelegramForbiddenError as e:
            logger.error(
                f"Ошибка при отправке сообщения в чат {subscriber.chat_id}: {e}"
            )
            # Удаляем подписчика, если отправка не удалась (например, пользователь заблокировал бота)
            await remove_subscriber(subscriber.chat_id)
            logger.info(f"Подписчик {subscriber.chat_id} удален из базы.")


async def main() -> None:
    await init_db()

    bot = Bot(
        token=settings.api_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    scheduler.add_job(send_daily_bird_photos, "cron", hour=13, args=[bot])
    scheduler.start()
    logger.info("Планировщик запущен.")

    try:
        logger.info("Бот запущен. Ожидание сообщений...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
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
