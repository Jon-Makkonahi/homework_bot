import logging
import os
import requests
import telegram
import time

from dotenv import load_dotenv


load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 300
ENDPOINT = os.getenv('ENDPOINT')

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}

logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    format='%(asctime)d, %(levelname)s, %(message)s'
)


def send_message(bot, message):
    """Отправка сообщения в телеграмм."""
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(url, current_timestamp):
    """Отправлять запрос к API домашки на эндпоинт."""
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    date = {'from_date': current_timestamp or time.time()}
    response = requests.get(url, headers=headers, params=date)
    if response.status_code == 200:
        return response.json()
    logging.error('Код не 200!')
    raise Exception


def parse_status(homework):
    """Проверка изменения статуса."""
    homework_name = homework['homework_name']
    verdict = HOMEWORK_STATUSES[homework['status']]
    message = f'Изменился статус проверки работы "{homework_name}". {verdict}'
    return message


def check_response(response):
    """Проверять полученный ответ на корректность."""
    homework = response.get('homeworks')[0]
    if homework['status'] not in HOMEWORK_STATUSES.keys():
        logging.error('Неправильный ключ')
        raise Exception
    if homework is None:
        logging.error('Домашка не изменилась')
        raise Exception
    return homework


def main():
    """Выполение."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
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
            time.sleep(RETRY_TIME)
            continue


if __name__ == '__main__':
    main()
