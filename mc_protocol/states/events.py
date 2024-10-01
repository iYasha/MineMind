import abc
from functools import cached_property

from mc_protocol.mc_types import VarInt, String, UShort, Long, SocketReader
from mc_protocol.states.enums import HandshakingNextState, ConnectionState


class Event(abc.ABC):
    packet_id: int
    state: ConnectionState


class InboundEvent(Event, abc.ABC):

    @classmethod
    @abc.abstractmethod
    async def from_stream(cls, reader: SocketReader) -> 'InboundEvent':
        pass


class OutboundEvent(Event, abc.ABC):

    @property
    def payload(self) -> bytes:
        return b''


# ----- Handshaking Events -----

class IntentionRequest(OutboundEvent):
    packet_id = 0x00
    state = ConnectionState.HANDSHAKING

    def __init__(
        self,
        protocol_version: int,
        server_address: str,
        server_port: int,
        next_state: HandshakingNextState,
    ) -> None:
        self.protocol_version = protocol_version
        self.server_address = server_address
        self.server_port = server_port
        self.next_state = next_state

    @property
    def payload(self) -> bytes:
        return (
            VarInt(self.protocol_version).bytes +
            String(self.server_address).bytes +
            UShort(self.server_port).bytes +
            self.next_state.value
        )


# ----- Status Events -----

class StatusRequest(OutboundEvent):
    packet_id = 0x00
    state = ConnectionState.STATUS


class PingRequest(OutboundEvent):
    packet_id = 0x01
    state = ConnectionState.STATUS

    def __init__(self, number: int) -> None:
        self.number = number

    @property
    def payload(self) -> bytes:
        return Long(self.number).bytes


class StatusResponse(InboundEvent):
    packet_id = 0x00
    state = ConnectionState.STATUS

    def __init__(self, response: str) -> None:
        self.response = response

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'InboundEvent':
        return cls(await String.from_stream(reader))


class PingResponse(InboundEvent):
    packet_id = 0x01
    state = ConnectionState.STATUS

    def __init__(self, number: int) -> None:
        self.number = number

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'PingResponse':
        return cls(await Long.from_stream(reader))
