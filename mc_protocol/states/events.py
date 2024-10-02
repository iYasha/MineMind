import abc
from functools import cached_property

from mc_protocol.mc_types import VarInt, String, UShort, Long
from mc_protocol.mc_types.base import SocketReader
from mc_protocol.states.enums import HandshakingNextState, ConnectionState


class Event(abc.ABC):
    packet_id: int
    state: ConnectionState

    def __repr__(self):
        return f'{self.__class__.__name__}({self.__dict__})'


class InboundEvent(Event, abc.ABC):

    @classmethod
    @abc.abstractmethod
    async def from_stream(cls, reader: SocketReader) -> 'InboundEvent':
        pass


class OutboundEvent(Event, abc.ABC):

    @property
    def payload(self) -> bytes:
        return b''
