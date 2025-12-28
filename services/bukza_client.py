import aiohttp
from typing import Optional, List, Dict, Any
from config import settings
import logging

logger = logging.getLogger(__name__)


class BukzaClient:
    """
    Клиент для работы с Bukza API.
    
    Примечание: Bukza работает в основном через вебхуки.
    Этот клиент используется для дополнительных запросов, если API доступен.
    """
    def __init__(self):
        self.api_url = settings.bukza_api_url
        self.api_key = settings.bukza_api_key
    
    async def send_feedback(self, booking_code: str, rating: int) -> bool:
        """
        Отправить обратную связь в Bukza (если API поддерживает).
        
        Примечание: Возможно, Bukza не имеет API для обратной связи.
        В этом случае данные сохраняются только в локальной БД.
        """
        logger.info(f"Feedback saved locally for booking {booking_code}: {rating}/5")
        
        # Если у Bukza есть API для обратной связи, раскомментируйте:
        # async with aiohttp.ClientSession() as session:
        #     headers = {"Authorization": f"Bearer {self.api_key}"}
        #     payload = {"booking_code": booking_code, "rating": rating}
        #     try:
        #         async with session.post(
        #             f"{self.api_url}/feedback",
        #             json=payload,
        #             headers=headers
        #         ) as response:
        #             return response.status == 200
        #     except Exception as e:
        #         logger.error(f"Error sending feedback to Bukza: {e}")
        #         return False
        
        return True


bukza_client = BukzaClient()
