class PasswordError(Exception):
    pass


class LengthError(PasswordError):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'LengthError, {0} '.format(self.message)
        else:
            return 'Пароль должен содержать более 8 символов'


class LetterError(PasswordError):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'LetterError, {0} '.format(self.message)
        else:
            return 'Пароль должен содержать строчные и прописные буквы'


class DigitError(PasswordError):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'DigitError, {0} '.format(self.message)
        else:
            return 'Пароль не должен содержать только цифры'


class DifferentError(PasswordError):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'DifferentError, {0} '.format(self.message)
        else:
            return 'Пароли не совпадают'
