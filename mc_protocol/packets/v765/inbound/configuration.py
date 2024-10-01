from mc_protocol.states.enums import ConnectionState
from mc_protocol.states.events import InboundEvent
from mc_protocol.mc_types import *

            
class FinishConfigurationResponse(InboundEvent):
    packet_id = 0x02
    state = ConnectionState.CONFIGURATION

            
class KeepAliveResponse(InboundEvent):
    packet_id = 0x03
    state = ConnectionState.CONFIGURATION

    def __init__(
        self,
        keep_alive_id: Long,
    ) -> None:
        self.keep_alive_id = keep_alive_id

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'KeepAliveResponse':
        return cls(
            keep_alive_id=await Long.from_stream(reader)
        )

        
class PingResponse(InboundEvent):
    packet_id = 0x04
    state = ConnectionState.CONFIGURATION

    def __init__(
        self,
        id: Int,
    ) -> None:
        self.id = id

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'PingResponse':
        return cls(
            id=await Int.from_stream(reader)
        )

        
class RemoveResourcePackResponse(InboundEvent):
    packet_id = 0x06
    state = ConnectionState.CONFIGURATION

    def __init__(
        self,
        uuid: UUID,
    ) -> None:
        self.uuid = uuid

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'RemoveResourcePackResponse':
        return cls(
            uuid=await UUID.from_stream(reader)
        )

        