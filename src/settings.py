from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.example", ".env"), extra="ignore", env_nested_delimiter="__"
    )

    api_token: str
    admin_id: str
    unsplash_api_key: str
    mongo_uri: str
    mongo_db_name: str


settings = Settings()
