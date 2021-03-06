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
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

RETRY_TIME = 600

STATUS_CHANGE = 'Изменился статус проверки работы "{homework_name}". {verdict}'
NO_ANSWER = (
    'Не удалось получить ответ от сервера:\n{error}\n'
    '{url}\n{headers}\n{params}'
)
NOT_SEND_MESSAGE = 'Не удалось отправить сообщение: {error}'
GLITCH = 'Сбой в работе программы: {error}'
INVALID_STATUS = 'Неожиданный статус д/з {status}'
ERROR = (
    'Ошибка {error} - {meaning}\n',
    '{url}\n{headers}\n{params}'
)
INVALID_CODE = (
    'Ошибка запроса - {code}\n',
    'Информация:\n{url}\n{headers}\n{params}'
)

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
    except Exception as error:
        logging.error(NOT_SEND_MESSAGE.format(error=error), exc_info=True)


def get_api_answer(url, current_timestamp):
    """Отправлять запрос к API домашки на эндпоинт."""
    try:
        date = {'from_date': current_timestamp}
        request_parametrs = dict(url=url, headers=HEADERS, params=date)
        response = requests.get(**request_parametrs)
    except requests.exceptions.RequestException as error:
        raise ConnectionError(NO_ANSWER.format(
            error=error,
            **request_parametrs
        ))
    response_json = response.json()
    for error in ('code', 'error'):
        if error in response_json:
            raise RuntimeError(ERROR.format(
                error=error,
                meaning=response_json[error],
                **request_parametrs
            ))
    if response.status_code != 200:
        raise RuntimeError(INVALID_CODE.format(
            code=response.status_code,
            **request_parametrs
        ))
    return response_json


def parse_status(homework):
    """Проверка изменения статуса."""
    return STATUS_CHANGE.format(
        homework_name=homework['homework_name'],
        verdict=HOMEWORK_VERDICTS[homework['status']]
    )


def check_response(response):
    """Проверять полученный ответ на корректность."""
    homework = response['homeworks'][0]
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise ValueError(INVALID_STATUS.format(status=homework['status']))
    return homework


def main():
    """Выполение."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - RETRY_TIME
    while True:
        try:
            response = get_api_answer(ENDPOINT, current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)
            current_timestamp = response.get('current_date', current_timestamp)
        except Exception as error:
            message = GLITCH.format(error)
            logging.error(message, stack_info=True)
            send_message(bot, message)
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s, %(levelname)s, %(lineno)s, %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(__file__ + '.log')
        ]
    )
    main()
