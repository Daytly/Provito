from data.PasswordErrors import LengthError, LetterError, DigitError, DifferentError
from PIL import Image


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


def crop_center(pil_img) -> Image:
    """
    Функция для обрезки изображения по центру.
    """
    img_width, img_height = pil_img.size
    _min_size = min(img_width, img_height)
    delta_x = (img_width - _min_size) // 2
    delta_y = (img_height - _min_size) // 2
    return pil_img.crop((delta_x, delta_y, img_width - delta_x, img_height - delta_y))
