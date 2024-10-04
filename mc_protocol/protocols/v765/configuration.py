from mc_protocol.client import Client
from mc_protocol.dispatcher import EventDispatcher
from mc_protocol.protocols.base import InteractionModule
from mc_protocol.protocols.enums import ConnectionState
from mc_protocol.protocols.v765.inbound.configuration import (
    FeatureFlagResponse,
    FinishConfigurationResponse,
    PluginMessageResponse,
    RegistryDataResponse,
    UpdateTagsResponse,
)
from mc_protocol.protocols.v765.outbound.configuration import FinishConfigurationRequest


class Configuration(InteractionModule):
    def __init__(self, client: Client):
        self.client = client

    @EventDispatcher.subscribe(PluginMessageResponse)
    async def _plugin_message(self, data: PluginMessageResponse):
        pass
        # print('plugin message', data.channel, len(data.data), 'bytes')

    @EventDispatcher.subscribe(FeatureFlagResponse)
    async def _feature_flag(self, data: FeatureFlagResponse):
        pass
        # print(f'feature flag {data.total_features=}')

    @EventDispatcher.subscribe(RegistryDataResponse)
    async def _registry_data(self, data: RegistryDataResponse):
        pass
        # TODO: Important to save this data for later use
        # dimension_name = data[minecraft:dimension_type][*][name]
        # min_y = data[minecraft:dimension_type][*][name][min_y]
        # height = data[minecraft:dimension_type][*][name][height]
        # print(f'Registry data {len(data.registry_codec)=} bytes')

    @EventDispatcher.subscribe(UpdateTagsResponse)
    async def _update_tags(self, data: UpdateTagsResponse):
        pass
        # print(f'Update tags {data.length}')

    @EventDispatcher.subscribe(FinishConfigurationResponse)
    async def _finish_configuration(self, data: FinishConfigurationResponse):
        await self.client.send_packet(FinishConfigurationRequest())
        self.client.state = ConnectionState.PLAY
