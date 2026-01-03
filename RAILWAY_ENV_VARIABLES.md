# Переменные окружения для Railway

Скопируйте эти переменные в Railway Dashboard → Variables

## Обязательные переменные

### Telegram Bot
```
BOT_TOKEN=8302336227:AAFuaVCPkW8jtIrTfsEs_9dxV72IyCGAS30
```

### Webhook (замените на ваш Railway URL)
```
WEBHOOK_HOST=https://u8gxvbk5.up.railway.app
WEBHOOK_PATH=/webhook/bukza
```

### Bukza API
```
BUKZA_API_URL=https://api.bukza.com
BUKZA_API_KEY=your_bukza_api_key_here
```

### Ссылки для отзывов
```
LINK_2GIS=https://2gis.ru/ufa/firm/70000001078004206
LINK_YANDEX_MAPS=https://yandex.ru/maps/org/pervoye_mesto/1234567890
```

## Информация о компании

### Контактные данные
```
COMPANY_ADDRESS=г. Уфа, Бакалинская улица, 27, ТКЦ ULTRA
COMPANY_PHONE=+7 (347) 266-00-00
COMPANY_EMAIL=info@firstplace-ufa.ru
COMPANY_WEBSITE=firstplace-ufa.ru
COMPANY_INSTAGRAM=@firstplace_ufa
COMPANY_HOURS=Ежедневно: 10:00 - 22:00
```

### Ссылка на онлайн-запись
```
BUKZA_BOOKING_URL=https://firstplace-ufa.ru/booking
```

## Опциональные переменные

### Канал поддержки (если есть)
```
SUPPORT_CHANNEL_ID=-100123456789
```
*Формат: -100 + ID канала. Получить можно через @userinfobot*

---

## Как добавить в Railway:

1. Откройте ваш проект в Railway
2. Перейдите в раздел **Variables**
3. Нажмите **+ New Variable**
4. Скопируйте каждую переменную (имя и значение)
5. Нажмите **Add** для каждой переменной
6. Railway автоматически перезапустит приложение

## Важно:

- **DATABASE_URL** - создаётся автоматически при добавлении PostgreSQL
- **PORT** - устанавливается автоматически Railway
- Не забудьте заменить `WEBHOOK_HOST` на ваш реальный Railway URL
- Обновите `BUKZA_API_KEY` на реальный ключ из админки Bukza

## Проверка:

После добавления всех переменных проверьте логи:
```
✅ Database initialized
✅ Scheduler started
✅ Telegram webhook set to: https://your-url.up.railway.app/webhook/telegram
```

Если всё работает - бот готов к использованию!
