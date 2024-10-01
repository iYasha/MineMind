from mc_protocol.states.enums import ConnectionState
from mc_protocol.states.events import InboundEvent
from mc_protocol.mc_types import *

            
class DisconnectResponse(InboundEvent):
    packet_id = 0x00
    state = ConnectionState.LOGIN

    def __init__(
        self,
        reason: String,
    ) -> None:
        self.reason = reason

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'DisconnectResponse':
        return cls(
            reason=await String.from_stream(reader)
        )

        
class CompressResponse(InboundEvent):
    packet_id = 0x03
    state = ConnectionState.LOGIN

    def __init__(
        self,
        threshold: VarInt,
    ) -> None:
        self.threshold = threshold

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'CompressResponse':
        return cls(
            threshold=await VarInt.from_stream(reader)
        )

        