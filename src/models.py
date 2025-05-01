from typing import Optional

from beanie import Document


class Subscriber(Document):
    chat_id: int
    bird_type: Optional[str] = "Yellowhammer"  # По умолчанию вид птицы

    class Settings:
        name = "subscribers"  # Название коллекции в MongoDB
