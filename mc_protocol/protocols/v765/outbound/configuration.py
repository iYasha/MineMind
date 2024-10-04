from mc_protocol.mc_types import UUID, Boolean, Byte, Int, Long, String, UByte, VarInt
from mc_protocol.protocols.enums import ConnectionState
from mc_protocol.protocols.protocol_events import OutboundEvent


class SettingsRequest(OutboundEvent):
    packet_id = 0x00
    state = ConnectionState.CONFIGURATION

    def __init__(
        self,
        locale: String,
        view_distance: Byte,
        chat_flags: VarInt,
        chat_colors: Boolean,
        skin_parts: UByte,
        main_hand: VarInt,
        enable_text_filtering: Boolean,
        enable_server_listing: Boolean,
    ) -> None:
        self.locale = locale
        self.view_distance = view_distance
        self.chat_flags = chat_flags
        self.chat_colors = chat_colors
        self.skin_parts = skin_parts
        self.main_hand = main_hand
        self.enable_text_filtering = enable_text_filtering
        self.enable_server_listing = enable_server_listing

    @property
    def payload(self) -> bytes:
        return (
            self.locale.bytes
            + self.view_distance.bytes
            + self.chat_flags.bytes
            + self.chat_colors.bytes
            + self.skin_parts.bytes
            + self.main_hand.bytes
            + self.enable_text_filtering.bytes
            + self.enable_server_listing.bytes
        )


class FinishConfigurationRequest(OutboundEvent):
    packet_id = 0x02
    state = ConnectionState.CONFIGURATION


class KeepAliveRequest(OutboundEvent):
    packet_id = 0x03
    state = ConnectionState.CONFIGURATION

    def __init__(
        self,
        keep_alive_id: Long,
    ) -> None:
        self.keep_alive_id = keep_alive_id

    @property
    def payload(self) -> bytes:
        return self.keep_alive_id.bytes


class PongRequest(OutboundEvent):
    packet_id = 0x04
    state = ConnectionState.CONFIGURATION

    def __init__(
        self,
        id: Int,
    ) -> None:
        self.id = id

    @property
    def payload(self) -> bytes:
        return self.id.bytes


class ResourcePackReceiveRequest(OutboundEvent):
    packet_id = 0x05
    state = ConnectionState.CONFIGURATION

    def __init__(
        self,
        uuid: UUID,
        result: VarInt,
    ) -> None:
        self.uuid = uuid
        self.result = result

    @property
    def payload(self) -> bytes:
        return self.uuid.bytes + self.result.bytes
