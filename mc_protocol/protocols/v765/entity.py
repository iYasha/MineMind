import enum
import math
import uuid
from typing import Any

from mc_protocol import DEBUG_PROTOCOL
from mc_protocol.client import Client
from mc_protocol.dispatcher import EventDispatcher
from mc_protocol.mc_types.base import Vector3
from mc_protocol.protocols.base import InteractionModule
from mc_protocol.protocols.utils import get_logger
from mc_protocol.protocols.v765.constants import ENTITIES
from mc_protocol.protocols.v765.inbound.play import (
    EntityLookResponse,
    EntityMoveLookResponse,
    EntityTeleportResponse,
    EntityVelocityResponse,
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


class MCMath:
    PI = math.pi
    PI_2 = math.pi * 2
    TO_RADIANS = PI / 180
    TO_DEGREES = 1 / TO_RADIANS
    FROM_NOTCH_BYTE = 360 / 256
    FROM_NOTCH_VEL = 1 / 8000

    @classmethod
    def euclidean_mod(cls, numerator: float, denominator: float) -> float:
        value = numerator % denominator
        return value + denominator if value < 0 else value

    @classmethod
    def to_radians(cls, degrees: float) -> float:
        return cls.TO_RADIANS * degrees

    @classmethod
    def to_degrees(cls, radians: float) -> float:
        return cls.TO_DEGREES * radians

    @classmethod
    def to_notchian_yaw(cls, yaw: float) -> float:
        return cls.to_degrees(cls.PI - yaw)

    @classmethod
    def from_notchian_yaw(cls, yaw: float) -> float:
        return cls.euclidean_mod(cls.PI - cls.to_radians(yaw), cls.PI_2)

    @classmethod
    def to_notchian_yaw_byte(cls, yaw: float) -> float:
        return cls.to_notchian_yaw(yaw) / cls.FROM_NOTCH_BYTE

    @classmethod
    def from_notchian_yaw_byte(cls, byte: int | float) -> float:
        return cls.from_notchian_yaw(byte * cls.FROM_NOTCH_BYTE)

    @classmethod
    def to_notchian_pitch(cls, pitch: float) -> float:
        return cls.to_degrees(-pitch)

    @classmethod
    def to_notchian_pitch_byte(cls, pitch: float) -> float:
        return cls.to_notchian_pitch(pitch) / cls.FROM_NOTCH_BYTE

    @classmethod
    def from_notchian_pitch_byte(cls, byte: int | float) -> float:
        return cls.from_notchian_pitch(byte * cls.FROM_NOTCH_BYTE)

    @classmethod
    def from_notchian_pitch(cls, pitch: float) -> float:
        return cls.euclidean_mod(cls.to_radians(-pitch) + cls.PI, cls.PI_2) - cls.PI

    @classmethod
    def from_notchian_velocity(cls, velocity: 'Vector3') -> 'Vector3':
        return Vector3(
            velocity.x * cls.FROM_NOTCH_VEL,
            velocity.y * cls.FROM_NOTCH_VEL,
            velocity.z * cls.FROM_NOTCH_VEL,
        )


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
        position: Vector3,
        velocity: Vector3,
        pitch: float,
        yaw: float,
        on_ground: bool = False,
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
        self.on_ground = on_ground

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
        yaw: int | float,
        pitch: int | float,
        position: Vector3,
        velocity: Vector3,
        on_ground: bool = False,
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
            velocity=MCMath.from_notchian_velocity(velocity),
            pitch=MCMath.from_notchian_pitch_byte(pitch),
            yaw=MCMath.from_notchian_yaw_byte(yaw),
            on_ground=on_ground,
            **kwargs,
        )

    def set_position_from_delta(self, dx: int, dy: int, dz: int):
        self.position.translate(
            dx / (128 * 32),
            dy / (128 * 32),
            dz / (128 * 32),
        )

    def set_position(self, x: float, y: float, z: float):
        self.position = Vector3(x, y, z)

    def set_rotation(self, yaw: int, pitch: int):
        self.yaw = MCMath.from_notchian_yaw_byte(yaw)
        self.pitch = MCMath.from_notchian_pitch_byte(pitch)

    def __repr__(self):
        return f'<Entity {self.display_name} {self.entity_id=}>'

    def set_velocity(self, velocity: Vector3):
        self.velocity = MCMath.from_notchian_velocity(velocity)


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
        position: Vector3,
        velocity: Vector3,
        pitch: float,
        yaw: float,
        username: str,
        on_ground: bool = False,
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
            on_ground=on_ground,
        )
        self.health = 20.0
        self.food = 20
        self.saturation = 5.0
        self.username = username
        self.eye_height = HitBox.PLAYER_EYE_HEIGHT.value

    def __repr__(self):
        return f'<Player {self.username} {self.entity_id=}>'


class Entities(InteractionModule):
    """
    Need to implement:
    - entity_equipment
    - bed
    - animation
    - collect
    - spawn_entity_experience_orb
    - entity_status
    - attach_entity
    - entity_metadata
    - entity_effect
    - remove_entity_effect
    - entity_update_attributes?
    - spawn_entity_weather
    - attach_entity
    - set_passengers
    """

    logger = get_logger('Entities')

    def __init__(self, client: Client):
        self.client = client
        self.entities: dict[int, Entity] = {}
        self._player_uuid_to_name: dict[uuid.UUID, str] = {}

    def create_bot(
        self,
        player_uuid: uuid.UUID,
        entity_id: int,
        username: str,
        yaw: float,
        pitch: float,
        position: Vector3,
        velocity: Vector3,
        on_ground: bool = False,
    ):
        entity_type_id = 124
        new_entity = Player.from_type_id(
            entity_uuid=player_uuid,
            entity_id=entity_id,
            entity_type_id=entity_type_id,
            yaw=yaw,
            pitch=pitch,
            position=position,
            velocity=velocity,
            username=username,
            on_ground=on_ground,
        )
        self.entities[entity_id] = new_entity
        self.logger.log(DEBUG_PROTOCOL, f'Bot entity {new_entity} spawned')

    @EventDispatcher.subscribe(PlayerInfoUpdateResponse)
    async def player_info_update(self, data: PlayerInfoUpdateResponse):
        for player in data.players:
            for player_action in player.player_actions:
                if player_action.action == PlayerAction.Action.ADD_PLAYER:
                    self._player_uuid_to_name[
                        player.uuid.uuid
                    ] = player_action.data.name.str  # type: ignore[union-attr]

    @EventDispatcher.subscribe(PlayerInfoRemoveResponse)
    async def player_info_remove(self, data: PlayerInfoRemoveResponse):
        for player_uuid in data.players:
            self._player_uuid_to_name.pop(player_uuid.uuid, None)

    @EventDispatcher.subscribe(SpawnEntityResponse)
    async def _entity_spawned(self, entity: SpawnEntityResponse):
        entity_class: type[Entity] | type[Player] = Entity
        kwargs = {}
        if entity.entity_id.int in self.entities:
            exist_entity = self.entities[entity.entity_id.int]
            exist_entity.set_position(entity.x.float, entity.y.float, entity.z.float)
            exist_entity.set_rotation(entity.yaw.int, entity.pitch.int)
            exist_entity.set_velocity(Vector3(entity.velocityx.int, entity.velocityy.int, entity.velocityz.int))
            self.logger.log(DEBUG_PROTOCOL, f'Entity {exist_entity} already exists. Updating it')
            return

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
            position=Vector3(entity.x.float, entity.y.float, entity.z.float),
            velocity=Vector3(entity.velocityx.int, entity.velocityy.int, entity.velocityz.int),
            on_ground=False,
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
        entity.set_position(data.x.float, data.y.float, data.z.float)
        entity.set_rotation(data.yaw.int, data.pitch.int)
        entity.on_ground = data.on_ground.bool
        self.logger.log(
            DEBUG_PROTOCOL,
            f'Entity {entity} teleported to {entity.position} {entity.yaw=} {entity.pitch=}',
        )

    @EventDispatcher.subscribe(RelEntityMoveResponse)
    async def _update_entity_position(self, data: RelEntityMoveResponse):
        entity = self.entities.get(data.entity_id.int)
        if not entity:
            self.logger.log(DEBUG_PROTOCOL, f'Entity {data.entity_id.int} moved, but not found in the list')
            return

        entity.set_position_from_delta(data.dx.int, data.dy.int, data.dz.int)
        entity.on_ground = data.on_ground.bool

        self.logger.log(DEBUG_PROTOCOL, f'Entity {entity} moved to {entity.position}')

    @EventDispatcher.subscribe(EntityMoveLookResponse)
    async def _update_entity_position_and_rotation(self, data: EntityMoveLookResponse):
        entity = self.entities.get(data.entity_id.int)
        if not entity:
            self.logger.log(DEBUG_PROTOCOL, f'Entity {data.entity_id.int} moved and rotated, but not found in the list')
            return

        entity.set_position_from_delta(data.dx.int, data.dy.int, data.dz.int)
        entity.set_rotation(data.yaw.int, data.pitch.int)
        entity.on_ground = data.on_ground.bool

        self.logger.log(
            DEBUG_PROTOCOL,
            f'Entity {entity} moved to {entity.position} and rotated to {entity.yaw=} {entity.pitch=}',
        )

    @EventDispatcher.subscribe(EntityLookResponse)
    async def _update_entity_rotation(self, data: EntityLookResponse):
        entity = self.entities.get(data.entity_id.int)
        if not entity:
            self.logger.log(DEBUG_PROTOCOL, f'Entity {data.entity_id.int} rotated, but not found in the list')
            return
        entity.set_rotation(data.yaw.int, data.pitch.int)
        entity.on_ground = data.on_ground.bool

        self.logger.log(DEBUG_PROTOCOL, f'Entity {entity} rotated to {entity.yaw=} {entity.pitch=}')

    @EventDispatcher.subscribe(EntityVelocityResponse)
    async def _update_entity_velocity(self, data: EntityVelocityResponse):
        entity = self.entities.get(data.entity_id.int)
        if not entity:
            self.logger.log(DEBUG_PROTOCOL, f'Entity {data.entity_id.int} rotated, but not found in the list')
            return
        entity.set_velocity(Vector3(data.velocityx.int, data.velocityy.int, data.velocityz.int))

        self.logger.log(DEBUG_PROTOCOL, f'Entity {entity} change velocity {entity.velocity}')

    def get_by_id(self, player_entity_id: int) -> Entity | Player | None:
        return self.entities.get(player_entity_id)
