from http import HTTPStatus
import logging
from logging import StreamHandler
import os
import sys
import time

import requests
from dotenv import load_dotenv
from telegram import Bot

from exceptions import (
    EmptyHomeworksDict, InvalidRequest, InvalidResponse, SendMessageError
)


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

HOMEWORK_NAME = 'homework_name'
HOMEWORK_STATUS = 'status'
HOMEWORKS_KEY = 'homeworks'
CURRENT_DATE_KEY = 'current_date'

LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'

# Инициализация логгера
logger = logging.getLogger(__name__)

# Задание базового конфига для логгера
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

# Создание хэндлера для записи в поток
handler = StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


def send_message(bot, message):
    """Функция отправляет сообщение юзеру в Telegram."""
    msg = bot.send_message(TELEGRAM_CHAT_ID, message)
    if not msg:
        error_msg = 'Сообщение не было отправлено'
        raise SendMessageError(error_msg)


def get_api_answer(current_timestamp):
    """
    Функиця делает запрос к API Практикум.Домашка.
    Возвращает дату в формате dict.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception:
        msg = ('Сервер недоступен. Проверьте правильность'
               f' эндпоинта [{ENDPOINT}].')
        logger.error(msg)
        raise ConnectionError(msg)

    api_response = response.json()
    status_code = response.status_code

    if 'error' in api_response:
        msg = api_response['error']['error']
        raise InvalidRequest(msg)
    elif ('code' in api_response and 'message' in api_response):
        msg = api_response['code'] + '. ' + api_response['message']
        raise InvalidRequest(msg)

    if status_code != HTTPStatus.OK:
        msg = f'Что-то пошло не так. Статус код API {status_code}.'
        raise ConnectionError(msg)

    return api_response


def check_response(response):
    """
    Функция проверяет ответ API на корректность.
    В случае успеха, функция возвращает список домашних работ.
    """
    if not response:
        msg = ('Ответ от API пуст. Проверьте корректность введенного'
               f' эндпоинта {ENDPOINT}, либо время запроса к API,'
               ' константа "RETRY_TIME".')
        raise InvalidResponse(msg)

    if HOMEWORKS_KEY not in response:
        msg = f'Отсутствует ожидаемый ключ "{HOMEWORKS_KEY}" в ответе API.'
        raise TypeError(msg)

    homeworks = response['homeworks']
    homeworks_type = type(homeworks)

    if not isinstance(homeworks, list):
        msg = (f'Полученный тип данных "{homeworks_type}" в ответе API'
               ' не соответствует ожидаемому типу данных "list".')
        raise TypeError(msg)

    if homeworks:
        return homeworks[0]
    else:
        msg = 'Отсутствует список домашних работ.'
        logger.info(msg)
        raise EmptyHomeworksDict(msg)


def parse_status(homework):
    """
    Функиця извлекает из конкретной домашней работы информацию для отправки.
    Измвлекаемая информация: homework_name, status.
    Возвращается строка для отправления юзеру.
    """
    if not homework:
        return 'Сегодня домашняя работа не отправлялась. Жду обновлений...'

    if HOMEWORK_NAME not in homework:
        msg = f'Отсутствует ожидаемый ключ "{HOMEWORK_NAME}" в ответе API.'
        raise KeyError(msg)

    elif HOMEWORK_STATUS not in homework:
        msg = (f'Отсутствует ожидаемый ключ "{HOMEWORK_STATUS}" '
               'в ответе API.')
        raise KeyError(msg)

    else:
        homework_name = homework.get(HOMEWORK_NAME)
        homework_status = homework.get(HOMEWORK_STATUS)

    if homework_status not in HOMEWORK_STATUSES:
        msg = ('Недокументированный статус домашней работы'
               f' "{homework_status}", обнаруженный в ответе API.')
        raise KeyError(msg)

    verdict = HOMEWORK_STATUSES.get(homework_status)
    return (f'Изменился статус проверки работы "{homework_name}".'
            f' {verdict}')


def check_tokens():
    """
    Функиця проверяет наличие токенов.
    В случае отсутствия одного из токенов, функция возвращает False,
    иначе True.
    """
    if not PRACTICUM_TOKEN:
        logger.critical(
            ('Отсутствует обязательная переменная окружения:'
             ' "PRACTICUM_TOKEN". Программа принудительно остановлена.')
        )
        return False
    elif not TELEGRAM_TOKEN:
        logger.critical(
            ('Отсутствует обязательная переменная окружения:'
             ' "TELEGRAM_TOKEN". Программа принудительно остановлена.')
        )
        return False
    elif not TELEGRAM_CHAT_ID:
        logger.critical(
            ('Сбой при отправке сообщения в Telegram.'
             ' Отсутствует обязательная переменная окружения:'
             ' "TELEGRAM_CHAT_ID". Программа принудительно остановлена.')
        )
        return False
    else:
        return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        exit()

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    previous_telegram_message = None
    previous_error_message = None

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)

            if message != previous_telegram_message:
                previous_telegram_message = message
                send_message(bot, message)
            else:
                logger.debug('В ответе отсутствуют новые статусы.')

            current_timestamp = response.get(CURRENT_DATE_KEY)

            if not isinstance(current_timestamp, int):
                msg = f'Неверный тип данных {CURRENT_DATE_KEY}'
                raise TypeError(msg)

            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)

            if message != previous_error_message:
                previous_error_message = message
                send_message(bot, message)

            time.sleep(RETRY_TIME)
        else:
            logger.debug('Бот работает без ошибок.')


if __name__ == '__main__':
    main()
