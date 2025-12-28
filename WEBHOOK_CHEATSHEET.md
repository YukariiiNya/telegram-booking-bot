# Шпаргалка по настройке вебхуков Bukza

## Вебхук 1: Новая запись

### Форма в Bukza:

**Название:**
```
Telegram - Новая запись
```

**URL запроса:**
```
https://your-domain.com/webhook/bukza?message=newrega&phone=%2B7%20%28{phone}%29
```

**Метод:** `POST`

**Тело запроса:**
```json
{
  "code": "{code}",
  "name": "{name}",
  "name_zone": "{name_zone}",
  "start": "{start}",
  "end": "{end}",
  "teh_end": "{teh_end}",
  "id_zakaz": "{id_zakaz}",
  "total_sum": "{total_sum}",
  "resource": "{resource}",
  "payed": "{payed}",
  "kolvo": "{kolvo}",
  "invoiceItems": [],
  "fields": []
}
```

---

## Вебхук 2: Отмена записи

### Форма в Bukza:

**Название:**
```
Telegram - Отмена записи
```

**URL запроса:**
```
https://your-domain.com/webhook/bukza?message=cancel&phone=%2B7%20%28{phone}%29
```

**Метод:** `POST`

**Тело запроса:**
```json
{
  "code": "{code}",
  "name": "{name}",
  "name_zone": "{name_zone}",
  "start": "{start}",
  "end": "{end}",
  "teh_end": "{teh_end}",
  "id_zakaz": "{id_zakaz}",
  "total_sum": "{total_sum}",
  "resource": "{resource}",
  "payed": "{payed}",
  "kolvo": "{kolvo}",
  "invoiceItems": [],
  "fields": []
}
```

---

## Важно!

1. **Замените `your-domain.com`** на ваш реальный домен (например, `bot.mycompany.ru`)
2. **Метод должен быть POST**, а не GET
3. **Галочку "Свои заголовки" НЕ ставить**
4. **JSON копируйте полностью**, включая фигурные скобки
5. Переменные в фигурных скобках `{phone}`, `{code}` и т.д. Bukza заменит автоматически

## Пример готового URL:

Если ваш домен `bot.salon.ru`, то URL будет:
```
https://bot.salon.ru/webhook/bukza?message=newrega&phone=%2B7%20%28{phone}%29
```
