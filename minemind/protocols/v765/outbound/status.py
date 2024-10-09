from minemind.mc_types import Long
from minemind.protocols.enums import ConnectionState
from minemind.protocols.protocol_events import OutboundEvent


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
