import asyncio
import inspect
from collections import defaultdict
from typing import TYPE_CHECKING, Callable, Coroutine, Literal, NamedTuple, Type, Union

from mc_protocol import DEBUG_TRACE
from mc_protocol.client import Client
from mc_protocol.mc_types import VarInt
from mc_protocol.mc_types.base import AsyncBytesIO, SocketReader
from mc_protocol.protocols.enums import ConnectionState
from mc_protocol.protocols.protocol_events import InboundEvent
from mc_protocol.protocols.utils import get_logger

if TYPE_CHECKING:
    from mc_protocol.protocols.base import InteractionModule

ListenerCallback = Union[
    Callable[
        [InboundEvent | SocketReader],
        Coroutine[None, None, None],
    ],
    Callable[
        ['InteractionModule', InboundEvent | SocketReader],
        Coroutine[None, None, None],
    ],
]

Listener = NamedTuple('Listener', [('event', Type[InboundEvent] | None), ('callback', ListenerCallback)])


class EventDispatcher:
    logger = get_logger('EventDispatcher')
    _callback_instances: dict[str, 'InteractionModule'] = {}
    _listeners: dict[str, dict[int | Literal['*'], list[Listener]]] = defaultdict(lambda: defaultdict(list))

    def __init__(self, client: Client):
        self.client = client
        self.bundle_packet = True
        self.bundle: list[Coroutine[None, None, None]] = []

    @classmethod
    def add_callback_instance(cls, instance: 'InteractionModule'):
        """
        We need this function to make it works:
        >>> @EventDispatcher.subscribe(KeepAliveResponse)
        >>> async def _keep_alive(self, reader: SocketReader):
        >>>     ...

        Because we need to pass `self` to the callback function.
        """
        cls._callback_instances[instance.__class__.__name__] = instance

    @classmethod
    def remove_callback_instance(cls, instance: 'InteractionModule'):
        cls._callback_instances.pop(instance.__class__.__name__, None)

    @classmethod
    def get_method_instance(cls, func: ListenerCallback) -> 'InteractionModule':
        class_name = func.__qualname__.split('.')[0]
        instance = cls._callback_instances.get(class_name)
        if instance is None:
            raise ValueError(f'Trying to get instance of {class_name} but it is not registered')
        return instance

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
                cls._listeners['*']['*'].append(Listener(None, func))
            elif all_events and state is not None:
                cls._listeners[state]['*'].append(Listener(None, func))

            return func

        return decorator

    async def invoke_callback(self, callback: ListenerCallback, event: InboundEvent | SocketReader):
        try:
            if 'self' in inspect.signature(callback).parameters:
                await callback(self.get_method_instance(callback), event)  # type: ignore[call-arg, arg-type]
            else:
                await callback(event)  # type: ignore[call-arg, arg-type]
        except Exception as e:
            packet_id = getattr(event, 'packet_id', None)
            self.logger.error(f'Error while invoking callback {callback} for event {packet_id}: {e}')

    async def submit_event(self, packet_id: VarInt, raw_data: AsyncBytesIO) -> None:
        listeners = (
            self._listeners[self.client.state].get(packet_id.int, [])
            + self._listeners['*'].get('*', [])
            + self._listeners[self.client.state].get('*', [])
        )
        if not listeners:
            self.logger.log(
                DEBUG_TRACE,
                f'[State={self.client.state}] Received packet {packet_id.hex} but no listeners are registered. '
                f'Packet len: {len(await raw_data.read(-1))}',
            )
            return

        self.logger.log(
            DEBUG_TRACE,
            f'[State={self.client.state}] Received packet {packet_id.hex} for {len(listeners)} listeners. '
            f'Length: {len(raw_data.getvalue())} bytes',
        )

        if len(listeners) == 1:  # Optimize for the common case
            listener = listeners[0]
            await self.invoke_callback(
                listener.callback,
                await listener.event.from_stream(raw_data) if listener.event else raw_data,
            )
            return

        data_value = raw_data.getvalue()
        await asyncio.gather(
            *[
                self.invoke_callback(
                    listener.callback,
                    (
                        await listener.event.from_stream(AsyncBytesIO(data_value))
                        if listener.event
                        else AsyncBytesIO(
                            data_value,
                        )
                    ),
                )
                for listener in listeners
            ],
        )

    async def run_forever(self):
        while True:
            packet_id, raw_data = await self.client.unpack_packet(self.client.reader)
            event = self.submit_event(packet_id, raw_data)

            is_bundle_delimiter = self.client.state == ConnectionState.PLAY and packet_id.int == 0

            if self.bundle_packet and is_bundle_delimiter:
                if self.bundle:  # End bundle
                    self.logger.log(DEBUG_TRACE, f'Free bundled package: {len(self.bundle)}')
                    [await bundled_event for bundled_event in self.bundle]
                    await event
                    self.bundle = []
                else:  # Start bundle
                    self.logger.log(DEBUG_TRACE, 'Bundle delimiter received, start bundling')
                    self.bundle.append(event)  # append packet
            elif self.bundle:  # we're bundling right now
                self.bundle.append(event)  # append packet
                bundle_length = len(self.bundle)
                self.logger.log(DEBUG_TRACE, f'Bundle packet, total length: {bundle_length}')
                if bundle_length > 32:
                    self.logger.log(DEBUG_TRACE, f'Bundle is too big, dropping it. Length: {bundle_length}')
                    [await bundled_event for bundled_event in self.bundle]
                    await event
                    self.bundle = []
                    self.bundle_packet = False
            else:  # Bundle is off and we process packet in regular
                await event
