# Деплой на VDS

## 1. Подготовка сервера

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить Python и зависимости
sudo apt install python3.11 python3.11-venv python3-pip nginx certbot python3-certbot-nginx -y

# Установить PostgreSQL (рекомендуется вместо SQLite)
sudo apt install postgresql postgresql-contrib -y
```

## 2. Настройка PostgreSQL

```bash
# Войти в PostgreSQL
sudo -u postgres psql

# Создать базу и пользователя
CREATE DATABASE firstplace_bot;
CREATE USER botuser WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE firstplace_bot TO botuser;
\q
```

## 3. Загрузка проекта

```bash
# Создать директорию
sudo mkdir -p /opt/firstplace-bot
cd /opt/firstplace-bot

# Клонировать репозиторий (или загрузить файлы)
git clone https://github.com/your-repo/firstplace-bot.git .

# Или загрузить через SCP с локальной машины:
# scp -r D:\bot\* user@your-server:/opt/firstplace-bot/
```

## 4. Настройка окружения

```bash
# Создать виртуальное окружение
python3.11 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Установить драйвер PostgreSQL
pip install asyncpg
```

## 5. Настройка .env

```bash
nano /opt/firstplace-bot/.env
```

```env
# Telegram Bot Token
BOT_TOKEN=8302336227:AAFuaVCPkW8jtIrTfsEs_9dxV72IyCGAS30

# Database (PostgreSQL)
DATABASE_URL=postgresql://botuser:your_secure_password@localhost:5432/firstplace_bot

# Bukza API
BUKZA_API_URL=https://api.bukza.com
BUKZA_API_KEY=demo_key

# Webhook (ваш домен)
WEBHOOK_HOST=https://bot.pervoe-mesto102.ru
WEBHOOK_PATH=/webhook/bukza

# Review Links
LINK_2GIS=https://2gis.ru/ufa/firm/70000001062371722
LINK_YANDEX_MAPS=https://yandex.ru/maps/org/pervoye_mesto/68437725658/

# Support Channel ID
SUPPORT_CHANNEL_ID=-1003579216287

# Company Info
COMPANY_ADDRESS=г. Уфа, Бакалинская улица, 27\nТКЦ ULTRA
COMPANY_PHONE=8(347)298-02-32
COMPANY_EMAIL=info@firstplace-ufa.ru
COMPANY_WEBSITE=pervoe-mesto102.ru
COMPANY_INSTAGRAM=@firstplace_ufa
COMPANY_HOURS=Ежедневно: 10:00 - 22:00
BUKZA_BOOKING_URL=https://app.bukza.com/#/24320/24018/catalog/27083
```

## 6. Настройка Nginx

```bash
sudo nano /etc/nginx/sites-available/firstplace-bot
```

```nginx
server {
    listen 80;
    server_name bot.pervoe-mesto102.ru;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
# Активировать конфиг
sudo ln -s /etc/nginx/sites-available/firstplace-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Получить SSL сертификат
sudo certbot --nginx -d bot.pervoe-mesto102.ru
```

## 7. Создание systemd сервиса

```bash
sudo nano /etc/systemd/system/firstplace-bot.service
```

```ini
[Unit]
Description=Firstplace Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/firstplace-bot
Environment=PATH=/opt/firstplace-bot/venv/bin
ExecStart=/opt/firstplace-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Установить права
sudo chown -R www-data:www-data /opt/firstplace-bot

# Запустить сервис
sudo systemctl daemon-reload
sudo systemctl enable firstplace-bot
sudo systemctl start firstplace-bot

# Проверить статус
sudo systemctl status firstplace-bot
```

## 8. Настройка Bukza Webhook

После деплоя обновите URL вебхука в Bukza:

**Новая запись:**
```
https://bot.pervoe-mesto102.ru/webhook/bukza?message=newrega&phone=[bukza_phone]&name=[bukza_first_name]
```

**Отмена:**
```
https://bot.pervoe-mesto102.ru/webhook/bukza?message=cancel&phone=[bukza_phone]&name=[bukza_first_name]
```

## 9. Полезные команды

```bash
# Логи бота
sudo journalctl -u firstplace-bot -f

# Перезапуск
sudo systemctl restart firstplace-bot

# Остановка
sudo systemctl stop firstplace-bot

# Подключение к БД
sudo -u postgres psql -d firstplace_bot
```

## 10. Миграция данных с SQLite

Если нужно перенести данные с локальной SQLite базы:

```bash
# На локальной машине - экспорт
sqlite3 bot_data.db .dump > backup.sql

# На сервере - импорт (нужно адаптировать SQL для PostgreSQL)
# Или использовать скрипт миграции
```

---

## Альтернатива: Railway (проще)

Если не хочешь возиться с VDS, можно задеплоить на Railway за 5 минут:

1. Зайди на https://railway.app
2. Подключи GitHub репозиторий
3. Добавь PostgreSQL из маркетплейса
4. Установи переменные окружения
5. Деплой автоматический

Подробнее в файле `RAILWAY_DEPLOY.md`
