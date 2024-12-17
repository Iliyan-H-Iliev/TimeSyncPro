from threading import local

_user = local()


def get_current_user():
    return getattr(_user, "value", None)


def set_current_user(user):
    _user.value = user


def clear_current_user():
    _user.value = None
