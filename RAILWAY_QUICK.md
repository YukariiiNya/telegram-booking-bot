# Railway - Быстрая шпаргалка

## За 5 минут

### 1. GitHub
```bash
git init
git add .
git commit -m "Initial"
git remote add origin https://github.com/username/repo.git
git push -u origin main
```

### 2. Railway
1. [railway.app](https://railway.app) → Login with GitHub
2. New Project → Deploy from GitHub → Выбрать репозиторий
3. + New → Database → PostgreSQL

### 3. Variables (в сервисе бота)
```
BOT_TOKEN=ваш_токен_от_botfather
BUKZA_API_URL=https://api.bukza.com
BUKZA_API_KEY=ваш_ключ
WEBHOOK_PATH=/webhook/bukza
LINK_2GIS=https://2gis.ru/ваш_салон
LINK_YANDEX_MAPS=https://yandex.ru/maps/ваш_салон
```

DATABASE_URL добавится автоматически!

### 4. Domain
Settings → Domains → Generate Domain

Скопируйте домен (например: `my-bot.up.railway.app`)

Добавьте переменную:
```
WEBHOOK_HOST=https://my-bot.up.railway.app
```

### 5. Bukza
URL для вебхука:
```
https://my-bot.up.railway.app/webhook/bukza?message=newrega&phone=%2B7%20%28{phone}%29
```

## Готово! 🎉

**Логи:** Deployments → последний деплой → View Logs

**Обновление:** `git push` → автоматический деплой

**Стоимость:** $5 бесплатно каждый месяц

---

📖 Полная инструкция: [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md)
