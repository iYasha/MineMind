import asyncio
import uuid
from contextlib import contextmanager, asynccontextmanager
from datetime import datetime

import pytz

from mc_protocol.client import Client
from mc_protocol.event_loop import EventLoop
from mc_protocol.mc_types import UUID, String, SocketReader, VarInt, Long
from mc_protocol.protocols.v765.configuration import Configuration
from mc_protocol.protocols.v765.inbound.login import LoginSuccessResponse, CompressResponse
from mc_protocol.protocols.v765.inbound.play import (
    PositionResponse, KeepAliveResponse, LoginResponse,
    CombatDeathResponse,
)
from mc_protocol.protocols.v765.outbound.login import LoginStartRequest, LoginAcknowledgedRequest
from mc_protocol.protocols.v765.outbound.play import (
    TeleportConfirmRequest, KeepAliveRequest, ClientCommandRequest,
    ChatMessageRequest,
)
from mc_protocol.protocols.v765.utils import handshake
from mc_protocol.states.enums import HandshakingNextState, ConnectionState


class OfflinePlayerNamespace:
    bytes = b'OfflinePlayer:'


class Player:
    # TODO: Add readable logs

    def __init__(self, client: Client):
        self.client = client
        self.configuration = None
        self.player_uuid = None
        self.player_entity_id = None
        EventLoop.subscribe_method(self._login_successful, LoginSuccessResponse)
        EventLoop.subscribe_method(self._set_threshold, CompressResponse)
        EventLoop.subscribe_method(self._synchronize_player_position, PositionResponse)
        EventLoop.subscribe_method(self._keep_alive, KeepAliveResponse)
        EventLoop.subscribe_method(self._start_playing, LoginResponse)
        EventLoop.subscribe_method(self._death, CombatDeathResponse)

    async def login(self, username: str) -> None:
        # TODO: currently only supports offline mode
        await handshake(self.client, HandshakingNextState.LOGIN)
        user_uuid = UUID(uuid.uuid3(OfflinePlayerNamespace, username))
        self.player_uuid = user_uuid

        request = LoginStartRequest(String(username), user_uuid)
        await self.client.send_packet(request)

    async def login_acknowledged(self):
        self.configuration = Configuration(self.client)
        await self.client.send_packet(LoginAcknowledgedRequest())
        self.client.state = ConnectionState.CONFIGURATION

    async def _login_successful(self, reader: SocketReader):
        data = await LoginSuccessResponse.from_stream(reader)
        print(f'[login_success] {data.username} {data.uuid}')
        await self.login_acknowledged()

    async def _set_threshold(self, reader: SocketReader):
        response = await CompressResponse.from_stream(reader)
        print('set threshold', response.threshold)
        self.client.threshold = response.threshold.int

    async def respawn(self):
        await self.client.send_packet(ClientCommandRequest(VarInt(0x00)))  # Perform respawn
        print('Respawned')

    async def _synchronize_player_position(self, reader: SocketReader):
        response = await PositionResponse.from_stream(reader)
        print(f'Teleportation confirmed. Position: {response.x=} {response.y=} {response.z=} {response.yaw=} {response.pitch=} {response.flags=} {response.teleport_id=}')
        await self.client.send_packet(TeleportConfirmRequest(response.teleport_id))
        await self.respawn()

    async def _keep_alive(self, reader: SocketReader):
        response = await KeepAliveResponse.from_stream(reader)
        print(f'Keep alive {response.keep_alive_id=}')
        await self.client.send_packet(KeepAliveRequest(response.keep_alive_id))

    async def _start_playing(self, reader: SocketReader):
        response = await LoginResponse.from_stream(reader)
        print(f'Login response {response.entity_id=}')
        self.player_entity_id = response.entity_id.int

    async def _death(self, reader: SocketReader):
        response = await CombatDeathResponse.from_stream(reader)
        print(f'Combat death {response.player_id=}')
        if response.player_id.int == self.player_entity_id:
            await self.respawn()

    async def chat_message(self, message: str):
        print(f'Sending chat message: {message}')
        await self.client.send_packet(ChatMessageRequest(
            message=String(message),
            timestamp=Long(round(datetime.now(tz=pytz.UTC).timestamp())),
            message_count=VarInt(0),
        ))

    @asynccontextmanager
    async def spawned(self):
        while not self.player_entity_id:
            await asyncio.sleep(0.000001)
        yield
