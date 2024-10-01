import abc
import asyncio
from collections import defaultdict
from typing import Literal, Type, Tuple, NamedTuple

from mc_protocol.client import Client
from mc_protocol.states.enums import ConnectionState
from mc_protocol.states.events import InboundEvent
from mc_protocol.utils import AsyncBytesIO

ALL_EVENTS = '*'


class Observer(abc.ABC):
    pass


Listener = NamedTuple('Listener', [('event', Type[InboundEvent] | None), ('callback', callable)])


class EventLoop:
    _listeners: dict[str, dict[int | Literal[ALL_EVENTS], list[Listener]]] = defaultdict(lambda: defaultdict(list))

    def __init__(self, client: Client):
        self.client = client

    @classmethod
    def subscribe_method(
        cls,
        func: callable,
        *events: Type[InboundEvent],
        state: ConnectionState | None = None,
        all_events: bool = False,
    ):
        for event in events:
            cls._listeners[event.state][event.packet_id].append(Listener(event, func))
        if all_events and state is None:
            cls._listeners[ALL_EVENTS][ALL_EVENTS].append(Listener(None, func))
        elif all_events and state is not None:
            cls._listeners[state][ALL_EVENTS].append(Listener(None, func))

    @classmethod
    def subscribe(
        cls,
        *events: Type[InboundEvent],
        state: ConnectionState | None = None,
        all_events: bool = False,
    ):
        def decorator(func):
            for event in events:
                cls._listeners[event.state][event.packet_id].append(Listener(event, func))
            if all_events and state is None:
                cls._listeners[ALL_EVENTS][ALL_EVENTS].append(Listener(None, func))
            elif all_events and state is not None:
                cls._listeners[state][ALL_EVENTS].append(Listener(None, func))

            return func

        return decorator

    async def run_forever(self):
        while True:
            print('Waiting for packet...')
            packet_id, data = await self.client.unpack_packet(self.client.reader)
            listeners = (
                self._listeners[self.client.state].get(packet_id.int, []) +
                self._listeners[ALL_EVENTS].get(ALL_EVENTS, []) +
                self._listeners[self.client.state].get(ALL_EVENTS, [])
            )
            if not listeners:
                print(
                    f'[State={self.client.state}] Received packet {packet_id.hex} but no listeners are registered. '
                    f'Data: {len(await data.read(-1))}'
                )
                continue

            # TODO: Add event auto-parsing
            if len(listeners) == 1:  # Optimize for the common case
                await listeners[0].callback(data)
                continue

            data_value = data.getvalue()
            try:
                await asyncio.gather(*[listener.callback(AsyncBytesIO(data_value)) for listener in listeners])
            except Exception as e:
                print(f'Error while handling packet {packet_id}: {e}')
