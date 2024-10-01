from mc_protocol.states.enums import ConnectionState
from mc_protocol.states.events import OutboundEvent
from mc_protocol.mc_types import *

        
class LoginStartRequest(OutboundEvent):
    packet_id = 0x00
    state = ConnectionState.LOGIN

    def __init__(
        self,
        username: String, playeruuid: UUID,
    ) -> None:
        self.username = username
        self.playeruuid = playeruuid

    @property
    def payload(self) -> bytes:
        return self.username.bytes + self.playeruuid.bytes

        
class LoginAcknowledgedRequest(OutboundEvent):
    packet_id = 0x03
    state = ConnectionState.LOGIN

            