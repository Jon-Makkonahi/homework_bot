import logging
import os
import time

from dotenv import load_dotenv
import requests
import telegram


load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600

MESSAGE = 'Изменился статус проверки работы "{homework_name}". {verdict}'
ERR = 'Не удалось получить ответ: {err}'
SEND_MESSAGE = 'Не удалось отправить сообщение: {e}'
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


def send_message(bot, message):
    """Отправка сообщения в телеграмм."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        print(SEND_MESSAGE.format(e=e))
        logging.error('Произошло исключение', exc_info=True)


def get_api_answer(url, current_timestamp):
    """Отправлять запрос к API домашки на эндпоинт."""
    try:
        date = {'from_date': current_timestamp}
        response = requests.get(url, headers=HEADERS, params=date)
        if response.status_code == 200:
            return response.json()
        raise ValueError('Код не 200!')
    except Exception as err:
        print(ERR.format(err=err))
        logging.error('Произошло исключение', exc_info=True)
    if 'code' in response:
        logging.error('Ошибка с сертификацией', exc_info=True)
        raise KeyError('Ошибка с сертификацией')
    if 'error' in response:
        logging.error('Ошибка по времени', exc_info=True)
        raise KeyError('Ошибка по времени')


def parse_status(homework):
    """Проверка изменения статуса."""
    return MESSAGE.format(
        homework_name = homework['homework_name'],
        verdict = HOMEWORK_VERDICTS[homework['status']]
    )


def check_response(response):
    """Проверять полученный ответ на корректность."""
    homework = response.get('homeworks')[0]
    if homework['status'] not in HOMEWORK_VERDICTS:
        logging.error('Неверный статус д/з', exc_info=True)
        raise KeyError('Неверный статус д/з')
    return homework


def main():
    """Выполение."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        current_timestamp = int(time.time()) - RETRY_TIME
        try:
            response = get_api_answer(ENDPOINT, current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            try:
                send_message(bot, message)
                time.sleep(RETRY_TIME)
            except Exception as error:
                print(f'Произошёл сбой бота {error}')

if __name__ == '__main__':
    main()
    logging.basicConfig(
        level=logging.ERROR,
        filename='homework_bot/program.log',
        format='%(asctime)s, %(levelname)s, %(lineno)s, %(message)s',
        handlers=[logging.StreamHandler(), 'handler.log']
    )