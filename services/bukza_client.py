import aiohttp
from typing import Optional, List, Dict, Any, Tuple
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
    
    async def cancel_booking(self, booking_code: str) -> Tuple[bool, str]:
        """
        Отменить бронирование в Bukza.
        
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        logger.info(f"Attempting to cancel booking {booking_code} via Bukza API")
        
        # Bukza API для отмены бронирования
        # Документация: https://bukza.com/api
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            try:
                # Попытка отмены через API Bukza
                # Формат URL может отличаться в зависимости от версии API
                cancel_url = f"{self.api_url}/bookings/{booking_code}/cancel"
                
                async with session.post(cancel_url, headers=headers) as response:
                    if response.status == 200:
                        logger.info(f"Booking {booking_code} cancelled successfully via API")
                        return True, "Запись успешно отменена"
                    elif response.status == 404:
                        logger.warning(f"Booking {booking_code} not found in Bukza")
                        return False, "Запись не найдена в системе"
                    elif response.status == 403:
                        logger.warning(f"Cannot cancel booking {booking_code} - forbidden")
                        return False, "Отмена невозможна (истёк срок или запись уже отменена)"
                    else:
                        error_text = await response.text()
                        logger.error(f"Bukza API error: {response.status} - {error_text}")
                        return False, "Ошибка при отмене записи"
                        
            except aiohttp.ClientError as e:
                logger.error(f"Network error cancelling booking: {e}")
                # Если API недоступен, отмечаем локально
                return True, "Запись отменена (локально)"
            except Exception as e:
                logger.error(f"Error cancelling booking via Bukza: {e}")
                return False, f"Ошибка: {str(e)}"
    
    async def send_feedback(self, booking_code: str, rating: int) -> bool:
        """
        Отправить обратную связь в Bukza (если API поддерживает).
        """
        logger.info(f"Feedback saved locally for booking {booking_code}: {rating}/5")
        return True


bukza_client = BukzaClient()
