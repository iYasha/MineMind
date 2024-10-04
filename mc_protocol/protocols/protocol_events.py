# TODO: Made these classes immutable to improve performance and not to parse the same data in dispatcher multiple times
import abc

from mc_protocol.mc_types.base import SocketReader
from mc_protocol.protocols.enums import ConnectionState


class Event(abc.ABC):
    packet_id: int
    state: ConnectionState

    def __repr__(self):
        return f'{self.__class__.__name__}({self.__dict__})'


class InboundEvent(Event, abc.ABC):
    @classmethod
    async def from_stream(cls, reader: SocketReader):
        return cls()


class OutboundEvent(Event, abc.ABC):
    @property
    def payload(self) -> bytes:
        return b''
