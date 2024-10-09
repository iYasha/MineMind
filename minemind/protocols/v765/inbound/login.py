from minemind.mc_types import UUID, String, VarInt
from minemind.mc_types.base import SocketReader
from minemind.protocols.enums import ConnectionState
from minemind.protocols.protocol_events import InboundEvent


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
            reason=await String.from_stream(reader),
        )


class LoginSuccessResponse(InboundEvent):
    packet_id = 0x02
    state = ConnectionState.LOGIN

    def __init__(
        self,
        uuid: UUID,
        username: String,
        number_of_properties: VarInt,
        # TODO: For properties we need Array type, but it's not implemented yet
    ) -> None:
        self.uuid = uuid
        self.username = username
        self.number_of_properties = number_of_properties

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'LoginSuccessResponse':
        return cls(
            uuid=await UUID.from_stream(reader),
            username=await String.from_stream(reader),
            number_of_properties=await VarInt.from_stream(reader),
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
            threshold=await VarInt.from_stream(reader),
        )
