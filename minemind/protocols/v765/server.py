from minemind.client import Client
from minemind.protocols.base import InteractionModule
from minemind.protocols.enums import HandshakingNextState
from minemind.protocols.utils import get_logger
from minemind.protocols.v765.handshake import handshake
from minemind.protocols.v765.inbound.status import ServerInfoResponse
from minemind.protocols.v765.outbound.status import PingStartRequest


class Server(InteractionModule):
    logger = get_logger('Server')

    def __init__(self, client: Client):
        self.client = client

    async def get_info(self) -> ServerInfoResponse:
        await handshake(self.client, HandshakingNextState.STATUS)
        await self.client.send_packet(PingStartRequest())

        packet_id, raw_data = await self.client.unpack_packet(self.client.reader)

        return await ServerInfoResponse.from_stream(raw_data)
