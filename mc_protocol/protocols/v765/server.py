import asyncio

from mc_protocol.client import Client
from mc_protocol.event_loop import EventLoop
from mc_protocol.mc_types import SocketReader
from mc_protocol.protocols.v765.inbound.status import ServerInfoResponse
from mc_protocol.protocols.v765.outbound.status import PingStartRequest
from mc_protocol.protocols.v765.utils import handshake
from mc_protocol.schemas import StatusResponse
from mc_protocol.states.enums import HandshakingNextState


class Server:
    info: StatusResponse = None

    def __init__(self, client: Client):
        self.client = client

    async def get_info(self, *, force_response: bool = False) -> StatusResponse | None:
        await handshake(self.client, HandshakingNextState.STATUS)
        await self.client.send_packet(PingStartRequest())

        # stupid way to return value using Observer pattern
        while self.info is None and force_response:
            await asyncio.sleep(0.00001)
        return self.info

    @staticmethod
    @EventLoop.subscribe(ServerInfoResponse)
    async def server_status(data: SocketReader):
        instance = await ServerInfoResponse.from_stream(data)
        Server.info = StatusResponse.model_validate_json(instance.response.str)


