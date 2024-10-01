import abc
from collections import defaultdict

from mc_protocol.enums import ConnectionState


class Observer(abc.ABC):
    pass


class EventLoop:

    _observers: dict[ConnectionState: list[Observer]] = defaultdict(list)

