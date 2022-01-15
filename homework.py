from pprint import pprint

import logging
from logging import StreamHandler
import os
import time
import sys

import requests
from dotenv import load_dotenv
from telegram import Bot

import exceptions

load_dotenv()

LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
# PRACTICUM_TOKEN = ''
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
# TELEGRAM_TOKEN = ''
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
# TELEGRAM_CHAT_ID = ''

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

# Инициализация логгера
logger = logging.getLogger(__name__)

logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)


def send_message(bot, message):
    """Функция отправляет сообщение юзеру в Telegram."""
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    """
    Функиця делает запрос к API Практикум.Домашка.
    Возвращает дату в формате dict.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params).json()
    return response


def check_response(response):
    """
    Функция проверяет ответ API на корректность.
    В случае успеха, функция возвращает список домашних работ.
    """
    if response:
        homeworks = response.get('homeworks')
        return homeworks


def parse_status(homework):
    """
    Функиця извлекает из конкретной домашней работы информацию для отправки.
    Измвлекаемая информация: homework_name, status.
    Возвращается строка для отправления юзеру.
    """
    if not homework:
        return 'Обновлений пока нет. Ждём-с...'

    for hw in homework:
        if HOMEWORK_NAME not in hw:
            msg = 'Ключ "homework_name" отсутствует в словаре.'
            # Добавить лог ?
            raise KeyError(msg)

        elif HOMEWORK_STATUS not in hw:
            msg = 'Ключ "status" отсутствует в словаре.'
            # Добавить лог ?
            raise KeyError(msg)

        else:
            homework_name = hw.get('homework_name')
            homework_status = hw.get('status')

        if homework_status not in HOMEWORK_STATUSES:
            msg = (f'Полученный статус задания "{homework_status}"'
                   ' не соответствует ожидаемому.')
            # Добавить лог ?
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
            ('Отсутствует обязательная переменная окружения:'
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

    while True:
        try:
            current_timestamp = 123
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)

            current_timestamp = 0
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            # НЕ ПОЯВЛЯЕТСЯ ЭТОТ ERROR В ЛОГАХ ???!
            # logger.error(message)
            send_message(bot, message)
            logger.info(
                f'Бот отправил сообщение "{message}"'
            )
            time.sleep(RETRY_TIME)
        else:
            ...

        handler = StreamHandler(stream=sys.stdout)
        logger.addHandler(handler)


if __name__ == '__main__':
    main()


"""
Обязательно должны логироваться такие события:

сбой при отправке сообщения в Telegram (уровень ERROR);

недоступность эндпоинта
https://practicum.yandex.ru/api/user_api/homework_statuses/ (уровень ERROR);

любые другие сбои при запросе к эндпоинту (уровень ERROR);

отсутствие ожидаемых ключей в ответе API (уровень ERROR)
!!!!! ПОЯВЛЕНИЕ В ЛОГАХ ?;

недокументированный статус домашней работы, обнаруженный
в ответе API (уровень ERROR) !!!! НЕ ПОЯВЛЯЕТСЯ В ЛОГАХ ???;

отсутствие в ответе новых статусов (уровень DEBUG).
"""
