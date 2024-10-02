import asyncio
import uuid
from contextlib import contextmanager, asynccontextmanager
from datetime import datetime
from decimal import Decimal

import pytz

from mc_protocol.client import Client
from mc_protocol.event_loop import EventLoop
from mc_protocol.mc_types import UUID, String, VarInt, Long, Boolean, UShort, UByte, Float, Short, Double
from mc_protocol.mc_types.base import SocketReader
from mc_protocol.protocols.v765.configuration import Configuration
from mc_protocol.protocols.v765.inbound.login import LoginSuccessResponse, CompressResponse
from mc_protocol.protocols.v765.inbound.play import (
    PositionResponse, KeepAliveResponse, LoginResponse,
    CombatDeathResponse, DamageEventResponse, RelEntityMoveResponse, UpdateHealthResponse, SpawnEntityResponse,
    EntityTeleportResponse, EntityMoveLookResponse, EntityLookResponse, RemoveEntityResponse,
)
from mc_protocol.protocols.v765.outbound.login import LoginStartRequest, LoginAcknowledgedRequest
from mc_protocol.protocols.v765.outbound.play import (
    TeleportConfirmRequest, KeepAliveRequest, ClientCommandRequest,
    ChatMessageRequest, InteractRequest, ArmAnimationRequest, SteerVehicleRequest, HeldItemSlotRequest, PositionRequest,
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

        self.health: float = 20.0
        self.food: int = 20
        self.saturation: float = 5.0

        # self.position =
        self.entities: dict[int, SpawnEntityResponse] = {}

        EventLoop.subscribe_method(self._login_successful, LoginSuccessResponse)
        EventLoop.subscribe_method(self._set_threshold, CompressResponse)
        EventLoop.subscribe_method(self._synchronize_player_position, PositionResponse)
        EventLoop.subscribe_method(self._keep_alive, KeepAliveResponse)
        EventLoop.subscribe_method(self._start_playing, LoginResponse)
        EventLoop.subscribe_method(self._death, CombatDeathResponse)
        EventLoop.subscribe_method(self._on_damage, DamageEventResponse)
        EventLoop.subscribe_method(self._update_entity_position, RelEntityMoveResponse)
        EventLoop.subscribe_method(self._update_health, UpdateHealthResponse)
        EventLoop.subscribe_method(self._entity_spawned, SpawnEntityResponse)
        EventLoop.subscribe_method(self._entity_teleport, EntityTeleportResponse)
        EventLoop.subscribe_method(self._update_entity_position_and_rotation, EntityMoveLookResponse)
        EventLoop.subscribe_method(self._update_entity_rotation, EntityLookResponse)
        EventLoop.subscribe_method(self._entities_removed, RemoveEntityResponse)
        # self.inventory = Inventory(self.player)
        # self.pvp = PVP(self.player)

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

    async def _set_player_position(self, x: Double, y: Double, z: Double, on_ground: bool = True):
        print(f'Setting player position to {x=} {y=} {z=}')
        await self.client.send_packet(PositionRequest(
            x=x,
            y=y,
            z=z,
            on_ground=Boolean(on_ground),
        ))

    async def _synchronize_player_position(self, reader: SocketReader):
        response = await PositionResponse.from_stream(reader)
        print(f'Teleportation confirmed. Position: {response.x=} {response.y=} {response.z=} {response.yaw=} {response.pitch=} {response.flags=} {response.teleport_id=}')
        await self.client.send_packet(TeleportConfirmRequest(response.teleport_id))
        await self.respawn()
        # await asyncio.sleep(1)
        # await self._set_player_position(Double(response.x.decimal + 2), Double(response.y.decimal - Decimal(1.62) - Decimal(0.38)), response.z)

    async def _keep_alive(self, reader: SocketReader):
        response = await KeepAliveResponse.from_stream(reader)
        # print(f'Keep alive {response.keep_alive_id=}')
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
        else:
            print(response)

    async def _on_damage(self, reader: SocketReader):
        response = await DamageEventResponse.from_stream(reader)

        if response.entity_id.int == self.player_entity_id:
            print(
                f'Player received damage from {response.source_type_id=} {response.source_cause_id=} {response.source_direct_id=}'
            )
            await self.attack(response.source_direct_id)
        else:
            print(
                f'Entity {response.entity_id.int} received damage from {response.source_type_id=} {response.source_cause_id=} {response.source_direct_id=}'
            )

    async def _update_health(self, reader: SocketReader):
        response = await UpdateHealthResponse.from_stream(reader)
        self.health = response.health.float
        self.food = response.food.int
        self.saturation = response.food_saturation.float
        print(f'Health: {self.health}/20.0 Food: {self.food}/20 Saturation: {self.saturation}/5.0')

    async def _entity_spawned(self, reader: SocketReader):
        response = await SpawnEntityResponse.from_stream(reader)
        self.entities[response.entity_id.int] = response
        # print(response)

    async def _entities_removed(self, reader: SocketReader):
        response = await RemoveEntityResponse.from_stream(reader)
        for entity_id in response.entity_ids:
            entity = self.entities.pop(entity_id.int, None)
            # print(f'[Remove] Entity {entity} removed')

    async def _entity_teleport(self, reader: SocketReader):
        response = await EntityTeleportResponse.from_stream(reader)
        entity = self.entities.get(response.entity_id.int)
        if not entity:
            print(f'[Teleport] Entity {response.entity_id.int} not found')
            return
        entity.set_new_position(response.x, response.y, response.z, response.pitch, response.yaw)
        # if entity.type.int == 124:  # player code
        #     print(f'[Teleport] Entity {response.entity_id.int} moved to {round(entity.x.float,3)=} {round(entity.y.float, 3)=} {round(entity.z.float, 3)=}')

    async def _update_entity_position(self, reader: SocketReader):
        response = await RelEntityMoveResponse.from_stream(reader)
        entity = self.entities.get(response.entity_id.int)
        if not entity:
            print(f'[Movement] Entity {response.entity_id.int} not found')
            return

        entity.new_position_from_delta(response.dx, response.dy, response.dz)
        # if entity.type.int == 124:  # player code
        #     print(f'[Movement] Entity {response.entity_id.int} moved to {round(entity.x.float,3)=} {round(entity.y.float, 3)=} {round(entity.z.float, 3)=}')

    async def _update_entity_position_and_rotation(self, reader: SocketReader):
        response = await EntityMoveLookResponse.from_stream(reader)
        entity = self.entities.get(response.entity_id.int)
        if not entity:
            print(f'[Movement] Entity {response.entity_id.int} not found')
            return

        entity.new_position_from_delta(response.dx, response.dy, response.dz)
        entity.set_new_position(yaw=response.yaw, pitch=response.pitch)
        # if entity.type.int == 124:  # player code
        #     print(f'[Movement] Entity {response.entity_id.int} moved to {round(entity.x.float,3)=} {round(entity.y.float, 3)=} {round(entity.z.float, 3)=}')

    async def _update_entity_rotation(self, reader: SocketReader):
        response = await EntityLookResponse.from_stream(reader)
        entity = self.entities.get(response.entity_id.int)
        if not entity:
            print(f'[Movement] Entity {response.entity_id.int} not found')
            return
        entity.set_new_position(yaw=response.yaw, pitch=response.pitch)

    async def set_active_slot(self, slot: int):
        request = HeldItemSlotRequest(
            slot_id=Short(slot),
        )
        print(f'Input', request)
        await self.client.send_packet(request)

    async def attack(self, entity_id: VarInt):
        request = InteractRequest(
            entity_id=entity_id,
            interact_type=InteractRequest.InteractType.ATTACK,
            sneaking=Boolean(False),
        )
        await self.client.send_packet(request)
        await self.client.send_packet(ArmAnimationRequest(ArmAnimationRequest.Hand.MAIN_HAND))

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
