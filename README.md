![Main Foodgram Workflow](https://github.com/QuickLike/foodgram/actions/workflows/main.yml/badge.svg)
# Проект Фудграм - это социальная сеть для любителей готовить.
Foodgram - социальная сеть, специально созданная для любителей готовить вкусную еду. Здесь вы можете делиться своими оригинальными и неповторимыми рецептами различных блюд.

## Как развернуть на сервере
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

3. Запустите Dockercompose
```
sudo docker compose -f docker-compose.production.yml pull
sudo docker compose -f docker-compose.production.yml down
sudo docker compose -f docker-compose.production.yml up -d
```
4. Сделайте миграции и соберите статику
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/ 
```
5. Загрузите фикстуры
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py loaddata data/ingredients.json
sudo docker compose -f docker-compose.production.yml exec backend python manage.py loaddata data/tags.json
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

## Как развернуть локально
1. Клонируйте репозиторий https://github.com/quicklike/foodgram
2. Перейдите в директорию /backend/
3. Создайте файл .env и добавьте в него необходимые переменные окружения
```
DJANGO_SECRET_KEY=<ключ Django>
DJANGO_DEBUG=<True/False>
DJANGO_ALLOWED_HOSTS=<разрешенные хосты, разделенные ЗАПЯТЫМИ ",">
DJANGO_DB=sqlite
```
4. Примените миграции
```
python manage.py migrate
python manage.py collectstatic
```
5. Загрузите фикстуры
```
python manage.py loaddata data/formatted_ingredients.json
python manage.py loaddata data/tags.json
```
6. Запустите локальный сервер
```
python manage.py runserver
```


## Стек

Backend:
  Python
  Django
  DRF

Frontend:
  JavaScript
  Node.js
  React

Сервер:
  nginx
  Gunicorn

Деплой
  Docker
  Docker compose

[Документация](https://github.com/QuickLike/foodgram/blob/main/docs/openapi-schema.yml)

[Власов Эдуард Витальевич](https://github.com/QuickLike)
