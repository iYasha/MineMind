import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

import pytz

from mc_protocol import DEBUG_GAME_EVENTS, DEBUG_PROTOCOL
from mc_protocol.client import Client
from mc_protocol.dispatcher import EventDispatcher
from mc_protocol.mc_types import UUID, Boolean, Double, Long, Short, String, VarInt
from mc_protocol.protocols.base import InteractionModule
from mc_protocol.protocols.enums import ConnectionState, HandshakingNextState
from mc_protocol.protocols.utils import get_logger
from mc_protocol.protocols.v765.configuration import Configuration
from mc_protocol.protocols.v765.handshake import handshake
from mc_protocol.protocols.v765.inbound.login import CompressResponse, LoginSuccessResponse
from mc_protocol.protocols.v765.inbound.play import (
    ChunkDataAndLightResponse,
    CombatDeathResponse,
    DamageEventResponse,
    EntityLookResponse,
    EntityMoveLookResponse,
    EntityTeleportResponse,
    KeepAliveResponse,
    LoginResponse,
    PositionResponse,
    RelEntityMoveResponse,
    RemoveEntityResponse,
    SetDefaultSpawnPositionResponse,
    SetTickingStateResponse,
    SpawnEntityResponse,
    StepTickResponse,
    UpdateHealthResponse,
    UpdateTimeResponse,
)
from mc_protocol.protocols.v765.outbound.login import LoginAcknowledgedRequest, LoginStartRequest
from mc_protocol.protocols.v765.outbound.play import (
    ArmAnimationRequest,
    ChatMessageRequest,
    ClientCommandRequest,
    HeldItemSlotRequest,
    InteractRequest,
    KeepAliveRequest,
    PositionRequest,
    TeleportConfirmRequest,
)


class OfflinePlayerNamespace:
    bytes = b'OfflinePlayer:'


class Player(InteractionModule):
    logger = get_logger('Player')

    def __init__(self, client: Client):
        self.client = client
        self.configuration = None
        self.player_uuid: UUID | None = None
        self.player_entity_id: int | None = None

        self.health: float = 20.0
        self.food: int = 20
        self.saturation: float = 5.0

        # self.position =
        self.entities: dict[int, SpawnEntityResponse] = {}

        # TODO: 0x25 Work with (Chunk Data and Update Light) - Looks like it's return block entities
        # self.inventory = Inventory(self.player)
        # self.pvp = PVP(self.player)

    async def login(self, username: str) -> None:
        # TODO: currently only supports offline mode
        await handshake(self.client, HandshakingNextState.LOGIN)
        # TODO: Argument 1 to "uuid3" has incompatible type "type[OfflinePlayerNamespace]"; expected "UUID"  [arg-type]
        user_uuid = UUID(uuid.uuid3(OfflinePlayerNamespace, username))  # type: ignore[arg-type]
        self.player_uuid = user_uuid

        request = LoginStartRequest(String(username), user_uuid)
        await self.client.send_packet(request)

    async def login_acknowledged(self):
        self.configuration = Configuration(self.client)
        await self.client.send_packet(LoginAcknowledgedRequest())
        self.client.state = ConnectionState.CONFIGURATION

    @EventDispatcher.subscribe(LoginSuccessResponse)
    async def _login_successful(self, data: LoginSuccessResponse):
        self.logger.log(DEBUG_GAME_EVENTS, f'User {data.username} logged in successfully!')
        await self.login_acknowledged()

    @EventDispatcher.subscribe(ChunkDataAndLightResponse)
    async def _update_chunk_and_light_data(self, data: ChunkDataAndLightResponse):
        pass

    @EventDispatcher.subscribe(CompressResponse)
    async def _set_threshold(self, data: CompressResponse):
        self.logger.log(DEBUG_PROTOCOL, f'Compression activated. Threshold set to {data.threshold.int}')
        self.client.threshold = data.threshold.int

    @EventDispatcher.subscribe(UpdateTimeResponse)
    async def _game_tick(self, data: UpdateTimeResponse):
        pass

    @EventDispatcher.subscribe(SetDefaultSpawnPositionResponse)
    async def _set_default_spawn_position(self, data: SetDefaultSpawnPositionResponse):
        pass

    @EventDispatcher.subscribe(SetTickingStateResponse)
    async def _set_ticking_state(self, data: SetTickingStateResponse):
        pass

    @EventDispatcher.subscribe(StepTickResponse)
    async def _step_tick(self, data: StepTickResponse):
        pass

    async def respawn(self):
        await self.client.send_packet(ClientCommandRequest(VarInt(0x00)))  # Perform respawn
        self.logger.log(DEBUG_GAME_EVENTS, 'Respawning...')

    async def _set_player_position(self, x: Double, y: Double, z: Double, on_ground: bool = True):
        await self.client.send_packet(
            PositionRequest(
                x=x,
                y=y,
                z=z,
                on_ground=Boolean(on_ground),
            ),
        )
        self.logger.log(DEBUG_GAME_EVENTS, f'Moved to {x=} {y=} {z=}')

    @EventDispatcher.subscribe(PositionResponse)
    async def _synchronize_player_position(self, data: PositionResponse):
        self.logger.log(
            DEBUG_PROTOCOL,
            f'Teleportation confirmed. Position: {data.x=} {data.y=} {data.z=} {data.yaw=} {data.pitch=} {data.flags=} {data.teleport_id=}',
        )
        await self.client.send_packet(TeleportConfirmRequest(data.teleport_id))
        # Respawn happens twice, on_death and here
        await self.respawn()
        # await asyncio.sleep(1)
        # await self._set_player_position(Double(response.x.decimal + 2), Double(response.y.decimal - Decimal(1.62) - Decimal(0.38)), response.z)

    @EventDispatcher.subscribe(KeepAliveResponse)
    async def _keep_alive(self, data: KeepAliveResponse):
        self.logger.log(DEBUG_PROTOCOL, f'Keep alive received: {data.keep_alive_id=}')
        await self.client.send_packet(KeepAliveRequest(data.keep_alive_id))

    @EventDispatcher.subscribe(LoginResponse)
    async def _start_playing(self, data: LoginResponse):
        self.player_entity_id = data.entity_id.int
        self.logger.log(DEBUG_PROTOCOL, f'Player entity id: {self.player_entity_id=}')

    @EventDispatcher.subscribe(CombatDeathResponse)
    async def _death(self, data: CombatDeathResponse):
        if data.player_id.int == self.player_entity_id:
            self.logger.log(DEBUG_GAME_EVENTS, f'Player died. Cause: {data.message}')
            await self.respawn()
        else:
            self.logger.log(DEBUG_GAME_EVENTS, f'Entity {data.player_id.int} died. Cause: {data.message}')

    @EventDispatcher.subscribe(DamageEventResponse)
    async def _on_damage(self, data: DamageEventResponse):
        if data.entity_id.int == self.player_entity_id:
            self.logger.log(DEBUG_GAME_EVENTS, f'Player received damage from {data.source_type_id}')
            await self.attack(data.source_direct_id)
        else:
            self.logger.log(
                DEBUG_GAME_EVENTS,
                f'Entity {data.entity_id.int} received damage from {data.source_type_id}',
            )

    @EventDispatcher.subscribe(UpdateHealthResponse)
    async def _update_health(self, data: UpdateHealthResponse):
        self.health = data.health.float
        self.food = data.food.int
        self.saturation = data.food_saturation.float
        self.logger.log(
            DEBUG_GAME_EVENTS,
            f'Health: {self.health}/20.0 Food: {self.food}/20 Saturation: {self.saturation}/5.0',
        )

    @EventDispatcher.subscribe(SpawnEntityResponse)
    async def _entity_spawned(self, data: SpawnEntityResponse):
        self.entities[data.entity_id.int] = data
        self.logger.log(DEBUG_PROTOCOL, f'Entity {data.entity_id.int} spawned')

    @EventDispatcher.subscribe(RemoveEntityResponse)
    async def _entities_removed(self, data: RemoveEntityResponse):
        for entity_id in data.entity_ids:
            self.entities.pop(entity_id.int, None)
            self.logger.log(DEBUG_PROTOCOL, f'Entity {entity_id.int} removed')

    @EventDispatcher.subscribe(EntityTeleportResponse)
    async def _entity_teleport(self, data: EntityTeleportResponse):
        entity = self.entities.get(data.entity_id.int)
        if not entity:
            self.logger.log(DEBUG_PROTOCOL, f'Entity {data.entity_id.int} teleported, but not found in the list')
            return
        entity.set_new_position(data.x, data.y, data.z, data.pitch, data.yaw)
        self.logger.log(DEBUG_PROTOCOL, f'Entity {data.entity_id.int} teleported to {data.x=} {data.y=} {data.z=}')

    @EventDispatcher.subscribe(RelEntityMoveResponse)
    async def _update_entity_position(self, data: RelEntityMoveResponse):
        entity = self.entities.get(data.entity_id.int)
        if not entity:
            self.logger.log(DEBUG_PROTOCOL, f'Entity {data.entity_id.int} moved, but not found in the list')
            return

        entity.new_position_from_delta(data.dx, data.dy, data.dz)
        self.logger.log(DEBUG_PROTOCOL, f'Entity {data.entity_id.int} moved to {entity.x=} {entity.y=} {entity.z=}')

    @EventDispatcher.subscribe(EntityMoveLookResponse)
    async def _update_entity_position_and_rotation(self, data: EntityMoveLookResponse):
        entity = self.entities.get(data.entity_id.int)
        if not entity:
            self.logger.log(DEBUG_PROTOCOL, f'Entity {data.entity_id.int} moved and rotated, but not found in the list')
            return

        entity.new_position_from_delta(data.dx, data.dy, data.dz)
        entity.set_new_position(yaw=data.yaw, pitch=data.pitch)
        self.logger.log(
            DEBUG_PROTOCOL,
            f'Entity {data.entity_id.int} moved to {entity.x=} {entity.y=} {entity.z=} and rotated to {data.yaw=} {data.pitch=}',
        )

    @EventDispatcher.subscribe(EntityLookResponse)
    async def _update_entity_rotation(self, data: EntityLookResponse):
        entity = self.entities.get(data.entity_id.int)
        if not entity:
            self.logger.log(DEBUG_PROTOCOL, f'Entity {data.entity_id.int} rotated, but not found in the list')
            return
        entity.set_new_position(yaw=data.yaw, pitch=data.pitch)
        self.logger.log(DEBUG_PROTOCOL, f'Entity {data.entity_id.int} rotated to {data.yaw=} {data.pitch=}')

    async def set_active_slot(self, slot: int):
        request = HeldItemSlotRequest(
            slot_id=Short(slot),
        )
        await self.client.send_packet(request)
        self.logger.log(DEBUG_GAME_EVENTS, f'Set active slot to {slot}')

    async def attack(self, entity_id: VarInt):
        request = InteractRequest(
            entity_id=entity_id,
            interact_type=InteractRequest.InteractType.ATTACK,
            sneaking=Boolean(False),
        )
        await self.client.send_packet(request)
        await self.client.send_packet(ArmAnimationRequest(ArmAnimationRequest.Hand.MAIN_HAND))
        self.logger.log(DEBUG_GAME_EVENTS, f'Attacking entity {entity_id.int}')

    async def chat_message(self, message: str):
        await self.client.send_packet(
            ChatMessageRequest(
                message=String(message),
                timestamp=Long(round(datetime.now(tz=pytz.UTC).timestamp())),
                message_count=VarInt(0),
            ),
        )
        self.logger.log(DEBUG_GAME_EVENTS, f'Sent chat message: {message}')

    @asynccontextmanager
    async def spawned(self):
        while not self.player_entity_id:
            await asyncio.sleep(0.000001)
        yield
