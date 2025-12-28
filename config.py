from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    
    # Telegram Bot
    bot_token: str
    
    # Database
    database_url: str
    
    # Bukza API
    bukza_api_url: str
    bukza_api_key: str
    
    # Webhook
    webhook_host: str
    webhook_path: str
    
    # Review Links
    link_2gis: str
    link_yandex_maps: str


settings = Settings()
