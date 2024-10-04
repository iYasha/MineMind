import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

import pytz

from mc_protocol.client import Client
from mc_protocol.dispatcher import EventDispatcher
from mc_protocol.mc_types import UUID, Boolean, Double, Long, Short, String, VarInt
from mc_protocol.protocols.base import InteractionModule
from mc_protocol.protocols.enums import ConnectionState, HandshakingNextState
from mc_protocol.protocols.v765.configuration import Configuration
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
from mc_protocol.protocols.v765.utils import handshake


class OfflinePlayerNamespace:
    bytes = b'OfflinePlayer:'


class Player(InteractionModule):
    # TODO: Add readable logs

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
        print(f'[login_success] {data.username} {data.uuid}')
        await self.login_acknowledged()

    @EventDispatcher.subscribe(ChunkDataAndLightResponse)
    async def _update_chunk_and_light_data(self, data: ChunkDataAndLightResponse):
        pass

    @EventDispatcher.subscribe(CompressResponse)
    async def _set_threshold(self, data: CompressResponse):
        print(hex(id(self)))
        print('set threshold', data.threshold)
        self.client.threshold = data.threshold.int

    @EventDispatcher.subscribe(UpdateTimeResponse)
    async def _game_tick(self, data: UpdateTimeResponse):
        pass
        # print(response)

    @EventDispatcher.subscribe(SetDefaultSpawnPositionResponse)
    async def _set_default_spawn_position(self, data: SetDefaultSpawnPositionResponse):
        pass
        # print(response)

    @EventDispatcher.subscribe(SetTickingStateResponse)
    async def _set_ticking_state(self, data: SetTickingStateResponse):
        print(data)

    @EventDispatcher.subscribe(StepTickResponse)
    async def _step_tick(self, data: StepTickResponse):
        print(data)

    async def respawn(self):
        await self.client.send_packet(ClientCommandRequest(VarInt(0x00)))  # Perform respawn
        print('Respawned')

    async def _set_player_position(self, x: Double, y: Double, z: Double, on_ground: bool = True):
        print(f'Setting player position to {x=} {y=} {z=}')
        await self.client.send_packet(
            PositionRequest(
                x=x,
                y=y,
                z=z,
                on_ground=Boolean(on_ground),
            ),
        )

    @EventDispatcher.subscribe(PositionResponse)
    async def _synchronize_player_position(self, data: PositionResponse):
        print(
            f'Teleportation confirmed. Position: {data.x=} {data.y=} {data.z=} {data.yaw=} {data.pitch=} {data.flags=} {data.teleport_id=}',
        )
        await self.client.send_packet(TeleportConfirmRequest(data.teleport_id))
        await self.respawn()
        # await asyncio.sleep(1)
        # await self._set_player_position(Double(response.x.decimal + 2), Double(response.y.decimal - Decimal(1.62) - Decimal(0.38)), response.z)

    @EventDispatcher.subscribe(KeepAliveResponse)
    async def _keep_alive(self, data: KeepAliveResponse):
        # print(f'Keep alive {response.keep_alive_id=}')
        await self.client.send_packet(KeepAliveRequest(data.keep_alive_id))

    @EventDispatcher.subscribe(LoginResponse)
    async def _start_playing(self, data: LoginResponse):
        print(f'Login response {data.entity_id=}')
        self.player_entity_id = data.entity_id.int

    @EventDispatcher.subscribe(CombatDeathResponse)
    async def _death(self, data: CombatDeathResponse):
        print(f'Combat death {data.player_id=}')
        if data.player_id.int == self.player_entity_id:
            await self.respawn()
        else:
            print(data)

    @EventDispatcher.subscribe(DamageEventResponse)
    async def _on_damage(self, data: DamageEventResponse):
        if data.entity_id.int == self.player_entity_id:
            print(
                f'Player received damage from {data.source_type_id=} {data.source_cause_id=} {data.source_direct_id=}',
            )
            await self.attack(data.source_direct_id)
        else:
            print(
                f'Entity {data.entity_id.int} received damage from {data.source_type_id=} {data.source_cause_id=} {data.source_direct_id=}',
            )

    @EventDispatcher.subscribe(UpdateHealthResponse)
    async def _update_health(self, data: UpdateHealthResponse):
        self.health = data.health.float
        self.food = data.food.int
        self.saturation = data.food_saturation.float
        print(f'Health: {self.health}/20.0 Food: {self.food}/20 Saturation: {self.saturation}/5.0')

    @EventDispatcher.subscribe(SpawnEntityResponse)
    async def _entity_spawned(self, data: SpawnEntityResponse):
        self.entities[data.entity_id.int] = data
        # print(response)

    @EventDispatcher.subscribe(RemoveEntityResponse)
    async def _entities_removed(self, data: RemoveEntityResponse):
        for entity_id in data.entity_ids:
            self.entities.pop(entity_id.int, None)
            # print(f'[Remove] Entity {entity} removed')

    @EventDispatcher.subscribe(EntityTeleportResponse)
    async def _entity_teleport(self, data: EntityTeleportResponse):
        entity = self.entities.get(data.entity_id.int)
        if not entity:
            print(f'[Teleport] Entity {data.entity_id.int} not found')
            return
        entity.set_new_position(data.x, data.y, data.z, data.pitch, data.yaw)
        # if entity.type.int == 124:  # player code
        #     print(f'[Teleport] Entity {response.entity_id.int} moved to {round(entity.x.float,3)=} {round(entity.y.float, 3)=} {round(entity.z.float, 3)=}')

    @EventDispatcher.subscribe(RelEntityMoveResponse)
    async def _update_entity_position(self, data: RelEntityMoveResponse):
        entity = self.entities.get(data.entity_id.int)
        if not entity:
            print(f'[Movement] Entity {data.entity_id.int} not found')
            return

        entity.new_position_from_delta(data.dx, data.dy, data.dz)
        # if entity.type.int == 124:  # player code
        #     print(f'[Movement] Entity {response.entity_id.int} moved to {round(entity.x.float,3)=} {round(entity.y.float, 3)=} {round(entity.z.float, 3)=}')

    @EventDispatcher.subscribe(EntityMoveLookResponse)
    async def _update_entity_position_and_rotation(self, data: EntityMoveLookResponse):
        entity = self.entities.get(data.entity_id.int)
        if not entity:
            print(f'[Movement] Entity {data.entity_id.int} not found')
            return

        entity.new_position_from_delta(data.dx, data.dy, data.dz)
        entity.set_new_position(yaw=data.yaw, pitch=data.pitch)
        # if entity.type.int == 124:  # player code
        #     print(f'[Movement] Entity {response.entity_id.int} moved to {round(entity.x.float,3)=} {round(entity.y.float, 3)=} {round(entity.z.float, 3)=}')

    @EventDispatcher.subscribe(EntityLookResponse)
    async def _update_entity_rotation(self, data: EntityLookResponse):
        entity = self.entities.get(data.entity_id.int)
        if not entity:
            print(f'[Movement] Entity {data.entity_id.int} not found')
            return
        entity.set_new_position(yaw=data.yaw, pitch=data.pitch)

    async def set_active_slot(self, slot: int):
        request = HeldItemSlotRequest(
            slot_id=Short(slot),
        )
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
        await self.client.send_packet(
            ChatMessageRequest(
                message=String(message),
                timestamp=Long(round(datetime.now(tz=pytz.UTC).timestamp())),
                message_count=VarInt(0),
            ),
        )

    @asynccontextmanager
    async def spawned(self):
        while not self.player_entity_id:
            await asyncio.sleep(0.000001)
        yield
