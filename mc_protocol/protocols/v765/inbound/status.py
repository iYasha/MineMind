from mc_protocol.mc_types import Long, String
from mc_protocol.mc_types.base import SocketReader
from mc_protocol.protocols.enums import ConnectionState
from mc_protocol.protocols.protocol_events import InboundEvent


class ServerInfoResponse(InboundEvent):
    packet_id = 0x00
    state = ConnectionState.STATUS

    def __init__(
        self,
        response: String,
    ) -> None:
        self.response = response

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'ServerInfoResponse':
        return cls(
            response=await String.from_stream(reader),
        )


class PingResponse(InboundEvent):
    packet_id = 0x01
    state = ConnectionState.STATUS

    def __init__(
        self,
        time: Long,
    ) -> None:
        self.time = time

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'PingResponse':
        return cls(
            time=await Long.from_stream(reader),
        )
