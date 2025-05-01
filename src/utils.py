import logging
import aiohttp
from src.settings import settings

logging.basicConfig(level=logging.INFO)


async def get_random_bird_image(bird_type: str) -> str | None:
    url = "https://api.unsplash.com/photos/random"
    params = {
        "query": bird_type,
        "client_id": settings.unsplash_api_key,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == aiohttp.http.HTTPStatus.OK:
                    data = await response.json()
                    return data["urls"]["regular"]
                else:
                    logging.error(f"Ошибка при запросе к Unsplash API: {response.status}")
                    return None
    except Exception as e:
        logging.error(f"Ошибка при получении изображения: {e}")
        return None