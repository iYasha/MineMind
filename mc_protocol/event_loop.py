import abc
import asyncio
from asyncio import StreamReader
from collections import defaultdict
from typing import Literal, Type, Tuple, NamedTuple

from mc_protocol.client import Client
from mc_protocol.mc_types import VarInt
from mc_protocol.mc_types.base import AsyncBytesIO
from mc_protocol.states.enums import ConnectionState
from mc_protocol.states.events import InboundEvent

ALL_EVENTS = '*'


class Observer(abc.ABC):
    pass


Listener = NamedTuple('Listener', [('event', Type[InboundEvent] | None), ('callback', callable)])


class EventLoop:
    _listeners: dict[str, dict[int | Literal[ALL_EVENTS], list[Listener]]] = defaultdict(lambda: defaultdict(list))

    def __init__(self, client: Client):
        self.client = client
        self.bundle_packet = True
        self.bundle = []

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

    async def submit_event(self, packet_id: VarInt, raw_data: AsyncBytesIO) -> None:
        listeners = (
            self._listeners[self.client.state].get(packet_id.int, []) +
            self._listeners[ALL_EVENTS].get(ALL_EVENTS, []) +
            self._listeners[self.client.state].get(ALL_EVENTS, [])
        )
        if not listeners:
            print(
                f'[State={self.client.state}] Received packet {packet_id.hex} but no listeners are registered. '
                f'Data: {len(await raw_data.read(-1))}'
            )
            return

        # TODO: Add event auto-parsing
        if len(listeners) == 1:  # Optimize for the common case
            await listeners[0].callback(raw_data)
            return

        data_value = raw_data.getvalue()
        try:
            await asyncio.gather(*[listener.callback(AsyncBytesIO(data_value)) for listener in listeners])
        except Exception as e:
            print(f'Error while handling packet {packet_id}: {e}')

    async def run_forever(self):
        while True:
            packet_id, raw_data = await self.client.unpack_packet(self.client.reader)
            event = self.submit_event(packet_id, raw_data)

            is_bundle_delimiter = self.client.state == ConnectionState.PLAY and packet_id.int == 0

            if self.bundle_packet and is_bundle_delimiter:
                if self.bundle:  # End bundle
                    # print('Free bundle', len(self.bundle))
                    [await bundled_event for bundled_event in self.bundle]
                    await event
                    self.bundle = []
                else:  # Start bundle
                    # print('Start bundle')
                    self.bundle.append(event)  # append packet
            elif self.bundle:  # we're bundling right now
                self.bundle.append(event)  # append packet
                # print(f'Bundled')
                if len(self.bundle) > 32:
                    # print(f'Stop bundle {len(self.bundle)}')
                    [await bundled_event for bundled_event in self.bundle]
                    await event
                    self.bundle = []
                    self.bundle_packet = False
            else:  # Bundle is off and we process packet in regular
                # print('Regular')
                await event

