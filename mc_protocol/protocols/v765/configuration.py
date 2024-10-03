from mc_protocol.client import Client
from mc_protocol.event_loop import EventLoop
from mc_protocol.mc_types.base import SocketReader
from mc_protocol.protocols.v765.inbound.configuration import (
    FeatureFlagResponse,
    FinishConfigurationResponse,
    PluginMessageResponse,
    RegistryDataResponse,
    UpdateTagsResponse,
)
from mc_protocol.protocols.v765.outbound.configuration import FinishConfigurationRequest
from mc_protocol.states.enums import ConnectionState


class Configuration:
    def __init__(self, client: Client):
        self.client = client
        EventLoop.subscribe_method(self._plugin_message, PluginMessageResponse)
        EventLoop.subscribe_method(self._feature_flag, FeatureFlagResponse)
        EventLoop.subscribe_method(self._registry_data, RegistryDataResponse)
        EventLoop.subscribe_method(self._update_tags, UpdateTagsResponse)
        EventLoop.subscribe_method(self._finish_configuration, FinishConfigurationResponse)

    async def _plugin_message(self, reader: SocketReader):
        await PluginMessageResponse.from_stream(reader)
        # print('plugin message', data.channel, len(data.data), 'bytes')

    async def _feature_flag(self, reader: SocketReader):
        await FeatureFlagResponse.from_stream(reader)
        # print(f'feature flag {data.total_features=}')

    async def _registry_data(self, reader: SocketReader):
        await RegistryDataResponse.from_stream(reader)
        # TODO: Important to save this data for later use
        # dimension_name = data[minecraft:dimension_type][*][name]
        # min_y = data[minecraft:dimension_type][*][name][min_y]
        # height = data[minecraft:dimension_type][*][name][height]
        # print(f'Registry data {len(data.registry_codec)=} bytes')

    async def _update_tags(self, reader: SocketReader):
        await UpdateTagsResponse.from_stream(reader)
        # print(f'Update tags {data.length}')

    async def _finish_configuration(self, reader: SocketReader):
        await self.client.send_packet(FinishConfigurationRequest())
        self.client.state = ConnectionState.PLAY
