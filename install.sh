#!/bin/bash
# Автоустановка бота на Ubuntu 22.04
# Запуск: curl -sSL https://raw.githubusercontent.com/YukariiiNya/telegram-booking-bot/main/install.sh | bash

set -e

echo "🚀 Установка Telegram бота..."

# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
sudo apt install -y python3.11 python3.11-venv python3-pip nginx certbot python3-certbot-nginx postgresql postgresql-contrib git

# Создание директории
sudo mkdir -p /opt/firstplace-bot
cd /opt/firstplace-bot

# Клонирование репозитория
sudo git clone https://github.com/YukariiiNya/telegram-booking-bot.git .

# Создание виртуального окружения
sudo python3.11 -m venv venv
sudo ./venv/bin/pip install --upgrade pip
sudo ./venv/bin/pip install -r requirements.txt
sudo ./venv/bin/pip install asyncpg

# Настройка PostgreSQL
sudo -u postgres psql -c "CREATE DATABASE firstplace_bot;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER botuser WITH PASSWORD 'changeme123';" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE firstplace_bot TO botuser;"

echo ""
echo "✅ Установка завершена!"
echo ""
echo "📝 Следующие шаги:"
echo "1. Отредактируй /opt/firstplace-bot/.env (скопируй из .env.example)"
echo "2. Измени пароль PostgreSQL в .env"
echo "3. Настрой домен и SSL"
echo "4. Запусти: sudo systemctl start firstplace-bot"
echo ""
echo "Подробная инструкция: /opt/firstplace-bot/VDS_DEPLOY.md"
