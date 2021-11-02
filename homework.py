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
    'Не удалось получить ответ от сервера: {error}\n'
    '{url}\n{headers}\n{params}'
)
NOT_SEND_MESSAGE = 'Не удалось отправить сообщение: {error}'
GLITCH = 'Сбой в работе программы: {error}'
INVALID_STATUS = 'Неверный статус д/з {status}'
INVALID_SERTIFICATION = 'Ошибка с сертификацией {error} - {meaning}'
FAIL_TIME = 'Ошибка по времени {error} - {meaning}'
INVALID_CODE = 'Неверный код ответа - {code}'

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
        response = requests.get(url, headers=HEADERS, params=date)
    except requests.exceptions.HTTPError as error:
        raise requests.exceptions.HTTPError(NO_ANSWER.format(
            error=error,
            url=url,
            headers=HEADERS,
            params=date
        ))
    response_json = response.json()
    cases = [
        ['code', INVALID_SERTIFICATION],
        ['error', FAIL_TIME]
    ]
    for error, text in cases:
        if error in response_json:
            raise ValueError(text.format(
                error=error,
                meaning=response_json[error]
            ))
    if response.status_code == 200:
        return response_json
    raise ValueError(INVALID_CODE.format(code=response.status_code))


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
    while True:
        current_timestamp = int(time.time()) - RETRY_TIME
        try:
            response = get_api_answer(ENDPOINT, current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)
            current_timestamp = response('current_date',)
        except Exception as error:
            message = GLITCH.format(error)
            send_message(bot, message)
            logging.error(message)
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
