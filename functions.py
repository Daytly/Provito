from data.PasswordErrors import LengthError, LetterError, DigitError, DifferentError


def check_password(password: str, password_again: str):
    if password != password_again:
        raise DifferentError()
    if len(password) < 8:
        raise LengthError
    if password.isdigit():
        raise DigitError()
    if password.isupper() or password.islower():
        raise LetterError()
    return True
