from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


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
    
    @field_validator('database_url')
    @classmethod
    def convert_database_url(cls, v: str) -> str:
        """Convert postgresql:// to postgresql+asyncpg:// for async support"""
        if v.startswith('postgresql://'):
            return v.replace('postgresql://', 'postgresql+asyncpg://', 1)
        return v

    @field_validator('webhook_host')
    @classmethod
    def ensure_https(cls, v: str) -> str:
        """Ensure webhook_host has https:// prefix"""
        if not v.startswith('http://') and not v.startswith('https://'):
            return f'https://{v}'
        return v


settings = Settings()
