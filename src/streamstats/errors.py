class StreamStatsError(Exception):
    """Общая ошибка программы."""

class InvalidEventError(StreamStatsError):
    """Неверные поля события."""

class InvalidTimestampError(InvalidEventError):
    """Неверная временная метка."""

class UnsupportedFormatError(StreamStatsError):
    """Неподдерживаемый формат файла."""

class CLIConfigError(StreamStatsError):
    """Неверные параметры командной строки."""
