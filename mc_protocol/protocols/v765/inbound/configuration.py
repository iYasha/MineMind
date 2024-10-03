from mc_protocol.mc_types import nbt
from mc_protocol.mc_types.base import SocketReader
from mc_protocol.states.enums import ConnectionState
from mc_protocol.states.events import InboundEvent
from mc_protocol.mc_types import *


class PluginMessageResponse(InboundEvent):
    packet_id = 0x00
    state = ConnectionState.CONFIGURATION

    def __init__(
        self,
        channel: String, data: bytes,
        # ByteArray haven't been implemented yet, so we use bytes instead
    ) -> None:
        self.channel = channel
        self.data = data

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'PluginMessageResponse':
        return cls(
            channel=await String.from_stream(reader),
            data=await reader.read(-1)
        )


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


class RegistryDataResponse(InboundEvent):
    packet_id = 0x05
    state = ConnectionState.CONFIGURATION

    def __init__(
        self,
        registry_codec: nbt.Compound,
    ) -> None:
        self.registry_codec = registry_codec

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'RegistryDataResponse':
        return cls(
            registry_codec=await nbt.NBT.from_stream(reader, is_anonymous=True)
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


class FeatureFlagResponse(InboundEvent):
    packet_id = 0x08
    state = ConnectionState.CONFIGURATION

    def __init__(
        self,
        total_features: VarInt,
        feature_flags: bytes,
    ) -> None:
        self.total_features = total_features
        self.feature_flags = feature_flags

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'FeatureFlagResponse':
        return cls(
            total_features=await VarInt.from_stream(reader),
            feature_flags=await reader.read(-1)
        )


class UpdateTagsResponse(InboundEvent):
    packet_id = 0x09
    state = ConnectionState.CONFIGURATION

    def __init__(
        self,
        length: VarInt,
        tags: bytes,
        # Array of Compound haven't been implemented yet, so we use bytes instead
    ) -> None:
        self.length = length
        self.tags = tags

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'UpdateTagsResponse':
        return cls(
            length=await VarInt.from_stream(reader),
            tags=await reader.read(-1)
        )

