class EmptyHomeworksDict(Exception):
    """Исключение для отсутствующего списка домашних работ."""
    pass


class EndpointError(Exception):
    """Исключение для некорректного Endpoint."""
    pass


class InvalidResponse(Exception):
    """Исключение для некорректного Response."""
    pass


class SendMessageError(Exception):
    """Исключение вызываемое при сбое отправки сообщения в Telegram."""
    pass
