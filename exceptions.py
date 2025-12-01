class SubjectValidationError(ValueError):
    """Пользовательское исключение для ошибок валидации названия предмета."""
    pass

class FileImportError(ValueError):
    """Пользовательское исключение для ошибок, связанных с импортом файла (размер, формат, пустота)."""
    pass
