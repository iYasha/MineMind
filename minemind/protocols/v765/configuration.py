from minemind import DEBUG_PROTOCOL
from minemind.client import Client
from minemind.dispatcher import EventDispatcher
from minemind.protocols.base import InteractionModule
from minemind.protocols.enums import ConnectionState
from minemind.protocols.utils import get_logger
from minemind.protocols.v765.inbound.configuration import (
    FeatureFlagResponse,
    FinishConfigurationResponse,
    PluginMessageResponse,
    UpdateTagsResponse,
)
from minemind.protocols.v765.outbound.configuration import FinishConfigurationRequest


class Configuration(InteractionModule):
    logger = get_logger('Configuration')

    def __init__(self, client: Client):
        self.client = client

    @EventDispatcher.subscribe(PluginMessageResponse)
    async def _plugin_message(self, data: PluginMessageResponse):
        self.logger.log(DEBUG_PROTOCOL, 'Received plugin message')

    @EventDispatcher.subscribe(FeatureFlagResponse)
    async def _feature_flag(self, data: FeatureFlagResponse):
        self.logger.log(DEBUG_PROTOCOL, 'Received feature flag')

    @EventDispatcher.subscribe(UpdateTagsResponse)
    async def _update_tags(self, data: UpdateTagsResponse):
        self.logger.log(DEBUG_PROTOCOL, 'Received tags update')

    @EventDispatcher.subscribe(FinishConfigurationResponse)
    async def _finish_configuration(self, data: FinishConfigurationResponse):
        await self.client.send_packet(FinishConfigurationRequest())
        self.client.state = ConnectionState.PLAY
        self.logger.log(DEBUG_PROTOCOL, 'Configuration finished. Switching to PLAY state')
