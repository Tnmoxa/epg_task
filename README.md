# Запуск через докер
В файле [docker-compose.yaml](docker-compose.yaml) необходимо указать значение переменных  
SMTP_EMAIL_FROM: "SMTP_EMAIL_FROM"  
SMTP_EMAIL_FROM_PASSWORD: "SMTP_EMAIL_FROM"  
```console
$ docker compose build
```

После этого можно запускать проект
```console
$ docker compose up
```
Сервис доступен по ссылке
"http://localhost:8080/"

Для запуска тестов необходимы переменные  
DATABASE_URL="sqlite+aiosqlite:///epg/database/database.db"  
SMTP_EMAIL_FROM - адрес почты для рассылки писем  
SMTP_EMAIL_FROM_PASSWORD - пароль почты для рассылки писем  
RATING_LIMIT_PER_DAY - количество оценок в день  
REDIS_URL - урл на редис  