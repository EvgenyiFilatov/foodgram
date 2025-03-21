## Проект Foodgram

Foodgram - это платформа, где пользователи могут делиться своими рецептами, добавлять рецепты других авторов в избранное и подписываться на предпочитаемых кулинаров. У зарегистрированных пользователей есть возможность воспользоваться функцией «Список покупок», которая позволяет формировать список ингредиентов, необходимых для приготовления выбранных блюд.

Сайт доступен по даресу: foodgramm.bounceme.net

## Технологический стек

- **Django**: Веб-фреймворк для разработки серверной части.
- **Django REST Framework**: Используется для создания API.
- **PostgreSQL**: СУБД для хранения и использования информации.
## Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
https://github.com/EvgenyiFilatov/foodgram.git
```

```
cd foodgram/backend
```

Cоздать и активировать виртуальное окружение:

```
python -m venv venv
```

```
source venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Импорт справочника ингридиентов из csv-файлов в базу данных:

```
python manage.py import_data_from_csv
```

Выполнить миграции:

```
python3 manage.py migrate
```
## Развертывание проекта на удалённом сервере

Копирование файла docker-compose.production.yml на сервер в директорию с приложением:

```
scp /путь/к/локальному/файлу username@server_ip:/путь/к/удаленной/папке
```

Создание в директории приложения файла с переменными окружения .env:

```
sudo nano .env

POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
DB_HOST=
DB_PORT=
SECRET_KEY=
DEBUG=
ALLOWED_HOSTS=
```

Установка на сервере docker и docker compose:

```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt install docker-compose-plugin 
```

Сборка контейнеров проекта:

```
sudo docker compose -f docker-compose.production.yml up -d
```

Применение миграций, сбор статики и копирование статики, импорт справочника ингридиентов:

```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic --no-input
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
sudo docker compose -f docker-compose.production.yml exec backend python manage.py import_data_from_csv
```
## Примеры запросов:

### Регистрация нового пользователя
Запрос:
```
POST .../api/users/

{
  "email": "vpupkin@yandex.ru",
  "username": "vasya.pupkin",
  "first_name": "Вася",
  "last_name": "Иванов",
  "password": "Qwerty123"
}
```
Ответ:
```
{
  "email": "vpupkin@yandex.ru",
  "id": 0,
  "username": "vasya.pupkin",
  "first_name": "Вася",
  "last_name": "Иванов"
}
```

### Добавление аватара
Запрос:
```
PUT .../api/users/me/avatar

{
  "avatar": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg=="
}
```
Ответ:
```
{
  "avatar": "http://foodgram.example.org/media/users/image.png"
}
```

## Авторы и разработчики:
Яндекс Практикум (автор проекта)

Евгений Филатов (backend developer)

Год разработки: 2025.
