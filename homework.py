import logging
import os
import time

import requests
from dotenv import load_dotenv
from telegram import Bot


load_dotenv()
# LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'

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
    response = requests.get(ENDPOINT, headers=HEADERS, payload=params).json()
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
    # Перечитать еще раз задание. Надо выдать 1 домашку.
    # Способы обработки пустой инфы с домашкой?
    # Достаточно ли того, что ниже?
    if homework:
        homework_name = homework.get('homework_name')
        homework_status = homework.get('status')
        verdict = HOMEWORK_STATUSES.get(homework_status)
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """
    Функиця проверяет наличие токенов.
    В случае отсутствия одного из токенов, функция возвращает False,
    иначе True.
    """
    if not PRACTICUM_TOKEN and TELEGRAM_TOKEN:
        return False
    return True


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = ...

            ...

            current_timestamp = ...
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
            time.sleep(RETRY_TIME)
        else:
            ...


if __name__ == '__main__':
    main()
