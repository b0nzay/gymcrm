import re

LOGIN_ERROR = 'Логин: 3-32 символа, латиница, цифры, точка или нижнее подчеркивание'


def normalize_username(value):
    nick = str(value or '').strip().lower()
    if not re.fullmatch(r'[a-z0-9._]{3,32}', nick):
        raise ValueError(LOGIN_ERROR)
    if nick.startswith('.') or nick.endswith('.') or '..' in nick:
        raise ValueError(LOGIN_ERROR)
    return nick
