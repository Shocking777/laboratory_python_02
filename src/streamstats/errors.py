class StreamStatsError(Exception):
    """Общая ошибка программы."""
    pass

class InvalidEventError(StreamStatsError):
    """Неверные поля события."""
    pass

class InvalidTimestampError(InvalidEventError):
    """Неверная временная метка."""
    pass

class UnsupportedFormatError(StreamStatsError):
    """Неподдерживаемый формат файла."""
    pass

class CLIConfigError(StreamStatsError):
    """Неверные параметры командной строки."""
    pass