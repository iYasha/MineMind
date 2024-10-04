import asyncio

from mc_protocol.client import Client
from mc_protocol.dispatcher import EventDispatcher
from mc_protocol.protocols.base import InteractionModule
from mc_protocol.protocols.enums import HandshakingNextState
from mc_protocol.protocols.v765.inbound.status import ServerInfoResponse
from mc_protocol.protocols.v765.outbound.status import PingStartRequest
from mc_protocol.protocols.v765.utils import handshake


class Server(InteractionModule):

    def __init__(self, client: Client):
        self.client = client
        self.info: ServerInfoResponse | None = None

    async def get_info(self, *, force_response: bool = False) -> ServerInfoResponse | None:
        await handshake(self.client, HandshakingNextState.STATUS)
        await self.client.send_packet(PingStartRequest())

        # stupid way to return value using Observer pattern
        while self.info is None and force_response:
            await asyncio.sleep(0.00001)
        return self.info

    @EventDispatcher.subscribe(ServerInfoResponse)
    async def server_status(self, data: ServerInfoResponse):
        self.info = data
