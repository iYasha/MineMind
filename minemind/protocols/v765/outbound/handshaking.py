from minemind.mc_types import String, UByte, UShort, VarInt
from minemind.protocols.enums import ConnectionState
from minemind.protocols.protocol_events import OutboundEvent


class SetProtocolRequest(OutboundEvent):
    packet_id = 0x00
    state = ConnectionState.HANDSHAKING

    def __init__(
        self,
        protocol_version: VarInt,
        server_host: String,
        server_port: UShort,
        next_state: VarInt,
    ) -> None:
        self.protocol_version = protocol_version
        self.server_host = server_host
        self.server_port = server_port
        self.next_state = next_state

    @property
    def payload(self) -> bytes:
        return self.protocol_version.bytes + self.server_host.bytes + self.server_port.bytes + self.next_state.bytes


class LegacyServerListPingRequest(OutboundEvent):
    packet_id = 0xFE
    state = ConnectionState.HANDSHAKING

    def __init__(
        self,
        data: UByte,
    ) -> None:
        self.data = data

    @property
    def payload(self) -> bytes:
        return self.data.bytes
