# Учебный проект "homework_bot"

Проект homework_bot - это один из проекто на Я.Практикуме, где нужно было написать 
Telegram-бота, который будет обращаться к API сервиса Практикум.Домашка и 
узнавать статус вашей домашней работы: взята ли ваша домашка в ревью, 
проверена ли она, а если проверена — то принял её ревьюер или вернул на доработку.

### Авторы:
- Daniil Bibikov (Jon-Makkonahi) https://github.com/Jon-Makkonahi

### Технологии:
- Python
- Djangо

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:Jon-Makkonahi/homework_bot.git
```

```
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```
