from mc_protocol.client import Client
from mc_protocol.dispatcher import EventDispatcher
from mc_protocol.protocols.base import InteractionModule
from mc_protocol.protocols.v765.inbound.play import LoginResponse


class World(InteractionModule):

    def __init__(self, client: Client):
        self.client = client

    @EventDispatcher.subscribe(LoginResponse)
    async def _start_playing(self, data: LoginResponse):
        pass
