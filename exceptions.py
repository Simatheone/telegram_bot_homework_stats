class ConnectionError(Exception):
    """Исключение для ошибки в запросе к API."""
    pass


class EmptyHomeworksDict(Exception):
    """Исключение для отсутствующего списка домашних работ."""
    pass


class EndpointError(Exception):
    """Исключение для некорректного Endpoint."""
    pass


class InvalidRequest(Exception):
    """Исключение для некорректного реквеста на API."""
    pass


class InvalidResponse(Exception):
    """Исключение для некорректного Response."""
    pass


class SendMessageError(Exception):
    """Исключение вызываемое при сбое отправки сообщения в Telegram."""
    pass
