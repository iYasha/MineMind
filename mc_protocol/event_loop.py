import abc
from collections import defaultdict
from typing import Literal

from mc_protocol.client import Client
from mc_protocol.states.enums import ConnectionState
from mc_protocol.states.events import InboundEvent

ALL_EVENTS = Literal['*']


class Observer(abc.ABC):
    pass


class EventLoop:
    _listeners: dict[int, dict[int | ALL_EVENTS, callable]] = defaultdict(list)

    def __init__(self, client: Client):
        self.client = client

    @classmethod
    def subscribe(cls, event: InboundEvent, state: ConnectionState | None = None):
        def decorator(func):
            def wrapper(*args, **kwargs):
                result = function(*args, **kwargs)
                return result
            return wrapper
        return decorator

    async def run_forever(self):
        while True:
            print('loop started')
            packet_id, data = await self.client.unpack_packet(self.client.reader)
            print(packet_id, data)

