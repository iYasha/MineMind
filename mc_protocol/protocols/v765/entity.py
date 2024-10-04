import enum
import uuid
from typing import Any

from mc_protocol import DEBUG_PROTOCOL
from mc_protocol.client import Client
from mc_protocol.dispatcher import EventDispatcher
from mc_protocol.protocols.base import InteractionModule
from mc_protocol.protocols.utils import get_logger
from mc_protocol.protocols.v765.constants import ENTITIES
from mc_protocol.protocols.v765.inbound.play import (
    EntityLookResponse,
    EntityMoveLookResponse,
    EntityTeleportResponse,
    PlayerAction,
    PlayerInfoRemoveResponse,
    PlayerInfoUpdateResponse,
    RelEntityMoveResponse,
    RemoveEntityResponse,
    SpawnEntityResponse,
)


class HitBox(float, enum.Enum):
    PLAYER_HEIGHT = 1.8
    CROUCH_HEIGHT = 1.5
    PLAYER_WIDTH = 0.6
    PLAYER_EYE_HEIGHT = 1.62
    CROUCH_EYE_HEIGHT = 1.27


class Position:

    def __init__(self, x: float, y: float, z: float):
        # TODO: Probably better to use a Decimal or just Vector3 class
        self.x = x
        self.y = y
        self.z = z


class Entity:

    def __init__(
        self,
        entity_uuid: uuid.UUID,
        entity_id: int,
        entity_type_id: int,
        entity_type: str,
        name: str,
        display_name: str,
        kind: str,
        height: float,
        width: float,
        position: Position,
        velocity: Position,
        pitch: float,
        yaw: float,
        **kwargs,
    ):
        self.entity_uuid = entity_uuid
        self.entity_id = entity_id
        self.entity_type_id = entity_type_id
        self.entity_type = entity_type
        self.name = name
        self.display_name = display_name
        self.kind = kind
        self.height = height
        self.width = width
        self.position = position
        self.velocity = velocity
        self.pitch = pitch
        self.yaw = yaw

    @classmethod
    def get_entity_type_by_id(cls, entity_type_id: int) -> dict[str, Any]:
        entity_data = ENTITIES.get(entity_type_id)
        if not entity_data:
            raise ValueError(f'Unknown entity type {entity_type_id}')
        return entity_data

    @classmethod
    def from_type_id(
        cls,
        entity_uuid: uuid.UUID,
        entity_id: int,
        entity_type_id: int,
        yaw: int,
        pitch: int,
        position: Position,
        velocity: Position,
        **kwargs,
    ) -> 'Entity':
        entity_data = ENTITIES.get(entity_type_id)
        if not entity_data:
            raise ValueError(f'Unknown entity type {entity_type_id}')
        return cls(
            entity_uuid=entity_uuid,
            entity_id=entity_id,
            entity_type_id=entity_type_id,
            entity_type=entity_data['type'],  # type: ignore[arg-type]
            name=entity_data['name'],  # type: ignore[arg-type]
            display_name=entity_data['displayName'],  # type: ignore[arg-type]
            kind=entity_data['category'],  # type: ignore[arg-type]
            height=entity_data['height'],  # type: ignore[arg-type]
            width=entity_data['width'],  # type: ignore[arg-type]
            position=position,
            velocity=velocity,
            pitch=pitch,
            yaw=yaw,
            **kwargs,
        )

    def __repr__(self):
        return f'<Entity {self.display_name} {self.entity_id=}>'


class Player(Entity):

    def __init__(
        self,
        entity_uuid: uuid.UUID,
        entity_id: int,
        entity_type_id: int,
        entity_type: str,
        name: str,
        display_name: str,
        kind: str,
        height: float,
        width: float,
        position: Position,
        velocity: Position,
        pitch: float,
        yaw: float,
        username: str,
    ):
        super().__init__(
            entity_uuid=entity_uuid,
            entity_id=entity_id,
            entity_type_id=entity_type_id,
            entity_type=entity_type,
            name=name,
            display_name=display_name,
            kind=kind,
            height=height,
            width=width,
            position=position,
            velocity=velocity,
            pitch=pitch,
            yaw=yaw,
        )
        self.health = 20.0
        self.food = 20
        self.saturation = 5.0
        self.username = username
        self.eye_height = HitBox.PLAYER_EYE_HEIGHT.value


class Entities(InteractionModule):
    logger = get_logger('Entities')

    def __init__(self, client: Client):
        self.client = client
        self.entities: dict[int, Entity] = {}
        self._player_uuid_to_name: dict[uuid.UUID, str] = {}

    @EventDispatcher.subscribe(PlayerInfoUpdateResponse)
    async def player_info_update(self, data: PlayerInfoUpdateResponse):
        for player in data.players:
            for player_action in player.player_actions:
                if player_action.action == PlayerAction.Action.ADD_PLAYER:
                    self._player_uuid_to_name[player.uuid.uuid] = player_action.data.name.str  # type: ignore[union-attr]

    @EventDispatcher.subscribe(PlayerInfoRemoveResponse)
    async def player_info_remove(self, data: PlayerInfoRemoveResponse):
        for player_uuid in data.players:
            self._player_uuid_to_name.pop(player_uuid.uuid, None)

    @EventDispatcher.subscribe(SpawnEntityResponse)
    async def _entity_spawned(self, entity: SpawnEntityResponse):
        entity_class: type[Entity] | type[Player] = Entity
        kwargs = {}
        entity_type = Entity.get_entity_type_by_id(entity.type.int)
        if entity_type['type'] == 'player':
            entity_class = Player
            kwargs = {'username': self._player_uuid_to_name.get(entity.object_uuid.uuid, 'Unknown')}
        new_entity = entity_class.from_type_id(
            entity_uuid=entity.object_uuid.uuid,
            entity_id=entity.entity_id.int,
            entity_type_id=entity.type.int,
            yaw=entity.yaw.int,
            pitch=entity.pitch.int,
            position=Position(entity.x.float, entity.y.float, entity.z.float),
            velocity=Position(entity.velocityx.int, entity.velocityy.int, entity.velocityz.int),
            **kwargs,
        )
        self.entities[entity.entity_id.int] = new_entity
        self.logger.log(DEBUG_PROTOCOL, f'Entity {new_entity} spawned')

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
        # entity.set_new_position(data.x, data.y, data.z, data.pitch, data.yaw)
        self.logger.log(DEBUG_PROTOCOL, f'Entity {data.entity_id.int} teleported to {data.x=} {data.y=} {data.z=}')

    @EventDispatcher.subscribe(RelEntityMoveResponse)
    async def _update_entity_position(self, data: RelEntityMoveResponse):
        entity = self.entities.get(data.entity_id.int)
        if not entity:
            self.logger.log(DEBUG_PROTOCOL, f'Entity {data.entity_id.int} moved, but not found in the list')
            return

        # entity.new_position_from_delta(data.dx, data.dy, data.dz)
        self.logger.log(DEBUG_PROTOCOL, f'Entity {data.entity_id.int} moved to {entity.position=}')

    @EventDispatcher.subscribe(EntityMoveLookResponse)
    async def _update_entity_position_and_rotation(self, data: EntityMoveLookResponse):
        entity = self.entities.get(data.entity_id.int)
        if not entity:
            self.logger.log(DEBUG_PROTOCOL, f'Entity {data.entity_id.int} moved and rotated, but not found in the list')
            return

        # entity.new_position_from_delta(data.dx, data.dy, data.dz)
        # entity.set_new_position(yaw=data.yaw, pitch=data.pitch)
        self.logger.log(
            DEBUG_PROTOCOL,
            f'Entity {data.entity_id.int} moved to {entity.position} and rotated to {data.yaw=} {data.pitch=}',
        )

    @EventDispatcher.subscribe(EntityLookResponse)
    async def _update_entity_rotation(self, data: EntityLookResponse):
        entity = self.entities.get(data.entity_id.int)
        if not entity:
            self.logger.log(DEBUG_PROTOCOL, f'Entity {data.entity_id.int} rotated, but not found in the list')
            return
        # entity.set_new_position(yaw=data.yaw, pitch=data.pitch)
        self.logger.log(DEBUG_PROTOCOL, f'Entity {data.entity_id.int} rotated to {data.yaw=} {data.pitch=}')
