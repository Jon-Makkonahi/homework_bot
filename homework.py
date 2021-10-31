import logging
import os
import time

from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
import requests
import telegram


load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = os.getenv('ENDPOINT')

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


def send_message(bot, message):
    """Отправка сообщения в телеграмм."""
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(url, current_timestamp):
    """Отправлять запрос к API домашки на эндпоинт."""
    date = {'from_date': current_timestamp}
    response = requests.get(url, headers=HEADERS, params=date)
    if response.status_code == 200:
        return response.json()
    raise ConnectionError('Код не 200!')


def parse_status(homework):
    """Проверка изменения статуса."""
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_response(response):
    """Проверять полученный ответ на корректность."""
    homework = response.get('homeworks')[0]
    if homework['status'] not in HOMEWORK_VERDICTS.keys():
        raise KeyError('Неправильный ключ')
    if homework is None:
        raise ValueError('Домашка не изменилась')
    return homework


def main():
    """Выполение."""
    logging.basicConfig(
        level=logging.ERROR,
        filename='program.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(lineno)s'
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    handler = RotatingFileHandler('program.log', maxBytes=50000000, backupCount=5)
    logger.addHandler(handler)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())-RETRY_TIME
    while True:
        try:
            response = get_api_answer(ENDPOINT, current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)

            
if __name__ == '__main__':
    main()
