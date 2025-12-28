# Развертывание Telegram-бота

## Архитектура системы

```
Bukza → Вебхук → Ваш сервер (Python) → Telegram Bot API → Клиенты
                      ↓
                  База данных
```

**Важно:** Нельзя отправлять вебхуки напрямую в Telegram! Нужен промежуточный сервер.

## Вариант 1: VPS сервер (Рекомендуется для продакшена)

### Шаг 1: Аренда VPS

Выберите провайдера:
- **Timeweb** - от 200₽/мес, русский интерфейс
- **Selectel** - от 250₽/мес
- **DigitalOcean** - от $6/мес
- **Hetzner** - от €4/мес

Минимальные требования:
- 1 CPU
- 1 GB RAM
- 10 GB SSD
- Ubuntu 22.04 или Debian 11

### Шаг 2: Подключение к серверу

```bash
ssh root@your-server-ip
```

### Шаг 3: Установка зависимостей

```bash
# Обновление системы
apt update && apt upgrade -y

# Установка Python и PostgreSQL
apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-contrib nginx certbot python3-certbot-nginx git

# Создание пользователя для бота
adduser botuser
usermod -aG sudo botuser
su - botuser
```

### Шаг 4: Клонирование проекта

```bash
cd /home/botuser
git clone <your-repo-url> telegram-bot
cd telegram-bot
```

### Шаг 5: Настройка виртуального окружения

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Шаг 6: Настройка PostgreSQL

```bash
sudo -u postgres psql

# В psql:
CREATE DATABASE booking_bot;
CREATE USER botuser WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE booking_bot TO botuser;
\q
```

### Шаг 7: Настройка .env

```bash
nano .env
```

Заполните:
```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql+asyncpg://botuser:your_secure_password@localhost:5432/booking_bot
BUKZA_API_URL=https://api.bukza.com
BUKZA_API_KEY=your_bukza_api_key
WEBHOOK_HOST=https://your-domain.com
WEBHOOK_PATH=/webhook/bukza
LINK_2GIS=https://2gis.ru/your-salon
LINK_YANDEX_MAPS=https://yandex.ru/maps/your-salon
```

### Шаг 8: Настройка домена и SSL

```bash
# Настройка Nginx
sudo nano /etc/nginx/sites-available/telegram-bot
```

Содержимое файла:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Активация конфигурации
sudo ln -s /etc/nginx/sites-available/telegram-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Получение SSL-сертификата
sudo certbot --nginx -d your-domain.com
```

### Шаг 9: Создание systemd сервиса

```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

Содержимое:
```ini
[Unit]
Description=Telegram Booking Bot
After=network.target postgresql.service

[Service]
Type=simple
User=botuser
WorkingDirectory=/home/botuser/telegram-bot
Environment="PATH=/home/botuser/telegram-bot/venv/bin"
ExecStart=/home/botuser/telegram-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Запуск сервиса
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# Проверка статуса
sudo systemctl status telegram-bot

# Просмотр логов
sudo journalctl -u telegram-bot -f
```

---

## Вариант 2: Railway.app (Быстрое развертывание)

### Преимущества:
- Бесплатно $5 кредитов каждый месяц
- Автоматический SSL
- Простое развертывание из GitHub
- Встроенная PostgreSQL

### Шаг 1: Подготовка проекта

Создайте файл `railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python main.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

Создайте файл `Procfile`:
```
web: python main.py
```

### Шаг 2: Развертывание

1. Зарегистрируйтесь на [railway.app](https://railway.app)
2. Создайте новый проект
3. Подключите GitHub репозиторий
4. Добавьте PostgreSQL из маркетплейса
5. Настройте переменные окружения в Railway:
   - `BOT_TOKEN`
   - `DATABASE_URL` (автоматически из PostgreSQL)
   - `BUKZA_API_KEY`
   - `WEBHOOK_HOST` (получите после развертывания)
   - `WEBHOOK_PATH=/webhook/bukza`
   - `LINK_2GIS`
   - `LINK_YANDEX_MAPS`

6. Railway автоматически развернет приложение

### Шаг 3: Получение URL

После развертывания Railway предоставит URL вида:
```
https://your-app-name.up.railway.app
```

Используйте этот URL в настройках вебхуков Bukza.

---

## Вариант 3: Heroku

### Шаг 1: Подготовка

Создайте `Procfile`:
```
web: python main.py
```

Создайте `runtime.txt`:
```
python-3.11.7
```

### Шаг 2: Развертывание

```bash
# Установка Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Логин
heroku login

# Создание приложения
heroku create your-bot-name

# Добавление PostgreSQL
heroku addons:create heroku-postgresql:mini

# Настройка переменных
heroku config:set BOT_TOKEN=your_token
heroku config:set BUKZA_API_KEY=your_key
heroku config:set WEBHOOK_HOST=https://your-bot-name.herokuapp.com
heroku config:set WEBHOOK_PATH=/webhook/bukza
heroku config:set LINK_2GIS=your_link
heroku config:set LINK_YANDEX_MAPS=your_link

# Развертывание
git push heroku main

# Просмотр логов
heroku logs --tail
```

---

## Вариант 4: Локальный сервер + ngrok (Только для тестирования!)

### Шаг 1: Установка ngrok

1. Скачайте с [ngrok.com](https://ngrok.com)
2. Зарегистрируйтесь и получите authtoken
3. Установите authtoken:
```bash
ngrok config add-authtoken your_token
```

### Шаг 2: Запуск бота локально

```bash
# Создайте .env файл
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Шаг 3: Запуск ngrok

В другом терминале:
```bash
ngrok http 8080
```

Вы получите URL вида:
```
https://abc123.ngrok.io
```

Используйте этот URL в настройках Bukza:
```
https://abc123.ngrok.io/webhook/bukza?message=newrega&phone=%2B7%20%28{phone}%29
```

**Важно:** 
- URL меняется при каждом перезапуске ngrok
- Не подходит для продакшена
- Только для разработки и тестирования

---

## Проверка развертывания

После развертывания проверьте:

1. **Доступность сервера:**
```bash
curl https://your-domain.com/webhook/bukza
```

2. **Логи бота:**
```bash
# VPS
sudo journalctl -u telegram-bot -f

# Railway/Heroku
# Смотрите в веб-интерфейсе

# Локально
# Логи в консоли
```

3. **База данных:**
```bash
# Подключитесь к PostgreSQL и проверьте таблицы
psql -U botuser -d booking_bot
\dt
```

4. **Telegram бот:**
Отправьте `/start` боту в Telegram

---

## Обновление бота

### VPS:
```bash
cd /home/botuser/telegram-bot
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart telegram-bot
```

### Railway/Heroku:
Просто сделайте `git push` - автоматически развернется

---

## Мониторинг

### Логи ошибок:
```bash
# VPS
sudo journalctl -u telegram-bot -p err -f

# Railway/Heroku
# Веб-интерфейс
```

### Проверка работы:
```bash
# Проверка процесса
ps aux | grep python

# Проверка порта
netstat -tulpn | grep 8080

# Проверка SSL
curl -I https://your-domain.com
```
