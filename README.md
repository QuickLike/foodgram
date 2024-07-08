![Main Foodgram Workflow](https://github.com/QuickLike/foodgram/actions/workflows/main.yml/badge.svg)
# Проект Фудграм - это социальная сеть для любителей готовить.
Foodgram - социальная сеть, специально созданная для любителей готовить вкусную еду. Здесь вы можете делиться своими оригинальными и неповторимыми рецептами различных блюд.

## Как развернуть
1. Скачайте docker-compose.production.yml из репозитория https://github.com/quicklike/foodgram
2. Создайте файл .env и добавьте в него необходимые переменные окружения
```
sudo nano .env
```
```
POSTGRES_DB=<БазаДанных>
POSTGRES_USER=<имя пользователя>
POSTGRES_PASSWORD=<пароль>
DB_NAME=<имя БазыДанных>
DB_HOST=db
DB_PORT=5432
DJANGO_SECRET_KEY=<ключ Django>
DJANGO_DEBUG=<True/False>
DJANGO_ALLOWED_HOSTS=<разрешенные хосты, разделенные ЗАПЯТЫМИ ",">
DJANGO_DB=<sqlite/postgresql>
```

4. Запустите Dockercompose
```
sudo docker compose -f docker-compose.production.yml pull
sudo docker compose -f docker-compose.production.yml down
sudo docker compose -f docker-compose.production.yml up -d
```
5. Сделайте миграции и соберите статику
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/ 
```
6. Загрузите фикстуры
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py loaddata data/ingredients.json
```

## Настройка CI/CD
Добавьте переменные репозитория GitHub
```
DOCKER_USERNAME - имя пользователя Docker Hub
DOCKER_PASSWORD - пароль от Docker Hub
HOST - ip сервера
USER - имя пользователя сервера
SSH_KEY - ключ ssh для доступа к удаленному серверу
SSH_PASSPHRASE - пароль ssh
TELEGRAM_TO - id пользователя TELEGRAM
TELEGRAM_TOKEN - TELEGRAM токен бота
```

## Стек

Backend:
  Django
  DRF

Frontend:
   JavaScript
   NodeJS
   React

Сервер:
  nginx
  Gunicorn

Деплой
  Docker
  Docker compose


## Автор QuickLike https://github.com/QuickLike
