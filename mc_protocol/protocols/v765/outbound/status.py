from mc_protocol.states.enums import ConnectionState
from mc_protocol.states.events import OutboundEvent
from mc_protocol.mc_types import *

        
class PingStartRequest(OutboundEvent):
    packet_id = 0x00
    state = ConnectionState.STATUS

            
class PingRequest(OutboundEvent):
    packet_id = 0x01
    state = ConnectionState.STATUS

    def __init__(
        self,
        time: Long,
    ) -> None:
        self.time = time

    @property
    def payload(self) -> bytes:
        return self.time.bytes

        