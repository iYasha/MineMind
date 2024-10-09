from minemind.mc_types import UUID, String
from minemind.protocols.enums import ConnectionState
from minemind.protocols.protocol_events import OutboundEvent


class LoginStartRequest(OutboundEvent):
    packet_id = 0x00
    state = ConnectionState.LOGIN

    def __init__(
        self,
        username: String,
        playeruuid: UUID,
    ) -> None:
        self.username = username
        self.playeruuid = playeruuid

    @property
    def payload(self) -> bytes:
        return self.username.bytes + self.playeruuid.bytes


class LoginAcknowledgedRequest(OutboundEvent):
    packet_id = 0x03
    state = ConnectionState.LOGIN
