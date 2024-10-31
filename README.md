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
