from http import HTTPStatus
import logging
from logging import StreamHandler
import os
import sys
import time

import requests
from dotenv import load_dotenv
from telegram import Bot

import exceptions

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

LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'

# Инициализация логгера
logger = logging.getLogger(__name__)

# Задание базового конфига для логгера
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)

# Создание хэндлера для записи в поток
handler = StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


def send_message(bot, message):
    """Функция отправляет сообщение юзеру в Telegram."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    if bot.send_message(TELEGRAM_CHAT_ID, message):
        logger.info('Юзеру отправлено сообщение в Telegram.')
    else:
        msg = ('Сбой при отправке сообщения в Telegram.')
        logger.error(msg)
        raise exceptions.SendMessageError(msg)


def get_api_answer(current_timestamp):
    """
    Функиця делает запрос к API Практикум.Домашка.
    Возвращает дату в формате dict.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)

    if response.status_code != HTTPStatus.OK:
        status_code = response.status_code

        msg = (f'Эндпоинт [{ENDPOINT}]({ENDPOINT}) недоступен.'
               f' Код ответа API: {status_code}')
        log_msg = (f'Сбой в работе программы: Эндпоинт {ENDPOINT} недоступен.'
                   f' Код ответа API: {status_code}')
        logger.error(log_msg)
        raise exceptions.EndpointError(msg)
    return response.json()


def check_response(response):
    """
    Функция проверяет ответ API на корректность.
    В случае успеха, функция возвращает список домашних работ.
    """
    if not response:
        msg = ('Ответ от API пуст. Проверьте корректность введенного'
               f' эндпоинта {ENDPOINT}, либо время запроса к API,'
               ' константа "RETRY_TIME".')
        logger.error(msg)
        raise exceptions.InvalidResponse(msg)

    if HOMEWORKS_KEY not in response:
        msg = f'Отсутствует ожидаемый ключ "{HOMEWORKS_KEY}" в ответе API.'
        logger.error(msg)
        raise KeyError(msg)

    homeworks = response['homeworks']
    homeworks_type = type(homeworks)

    if not isinstance(homeworks, list):
        msg = (f'Полученный тип данных "{homeworks_type}" в ответе API'
               ' не соответствует ожидаемому типу данных "list".')
        logger.error(msg)
        raise TypeError(msg)

    if homeworks:
        return homeworks[0]
    else:
        msg = 'Отсутствует список домашних работ.'
        logger.info(msg)
        raise exceptions.EmptyHomeworksDict(msg)


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
        logger.error(msg)
        raise KeyError(msg)

    elif HOMEWORK_STATUS not in homework:
        msg = (f'Отсутствует ожидаемый ключ "{HOMEWORK_STATUS}" '
               'в ответе API.')
        logger.error(msg)
        raise KeyError(msg)

    else:
        homework_name = homework.get(HOMEWORK_NAME)
        homework_status = homework.get(HOMEWORK_STATUS)

    if homework_status not in HOMEWORK_STATUSES:
        msg = ('Недокументированный статус домашней работы'
               f' "{homework_status}", обнаруженный в ответе API.')
        logger.error(msg)
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

    previous_telegram_message = []
    previous_error_message = []

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            if message not in previous_telegram_message:
                previous_telegram_message.append(message)
                send_message(bot, message)
            else:
                logger.debug('В ответе отсутствуют новые статусы.')

            current_timestamp = 1
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message not in previous_error_message:
                previous_error_message.append(message)
                send_message(bot, message)

            time.sleep(RETRY_TIME)
        else:
            logger.debug('Бот работает без ошибок.')


if __name__ == '__main__':
    main()
