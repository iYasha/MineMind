import logging


def get_logger(name: str = 'MineMind') -> logging.Logger:
    return logging.getLogger(name)


class ConnectionClosed(Exception):
    pass
