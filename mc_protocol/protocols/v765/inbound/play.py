from decimal import Decimal
from typing import Optional

from mc_protocol.mc_types.base import SocketReader
from mc_protocol.states.enums import ConnectionState
from mc_protocol.states.events import InboundEvent
from mc_protocol.mc_types import *


class SpawnEntityResponse(InboundEvent):
    packet_id = 0x01
    state = ConnectionState.PLAY

    def __init__(
        self,
        entity_id: VarInt, object_uuid: UUID, type: VarInt, x: Double, y: Double, z: Double, pitch: Byte, yaw: Byte,
        head_pitch: Byte, object_data: VarInt, velocityx: Short, velocityy: Short, velocityz: Short,
    ) -> None:
        self.entity_id = entity_id
        self.object_uuid = object_uuid
        self.type = type
        self.x = x
        self.y = y
        self.z = z
        self.pitch = pitch
        self.yaw = yaw
        self.head_pitch = head_pitch
        self.object_data = object_data
        self.velocityx = velocityx
        self.velocityy = velocityy
        self.velocityz = velocityz

    def set_new_position(self, x: Double | None = None, y: Double | None = None, z: Double  | None = None, pitch: Byte | None = None, yaw: Byte | None = None):
        if x is not None:
            self.x = x
        if y is not None:
            self.y = y
        if z is not None:
            self.z = z
        if pitch is not None:
            self.pitch = pitch
        if yaw is not None:
            self.yaw = yaw

    def new_position_from_delta(self, dx: Short, dy: Short, dz: Short):
        self.x = Double((Decimal(dx.int) / 128 + self.x.decimal * 32) / 32)
        self.y = Double((Decimal(dy.int) / 128 + self.y.decimal * 32) / 32)
        self.z = Double((Decimal(dz.int) / 128 + self.z.decimal * 32) / 32)

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'SpawnEntityResponse':
        return cls(
            entity_id=await VarInt.from_stream(reader), object_uuid=await UUID.from_stream(reader),
            type=await VarInt.from_stream(reader), x=await Double.from_stream(reader),
            y=await Double.from_stream(reader), z=await Double.from_stream(reader),
            pitch=await Byte.from_stream(reader), yaw=await Byte.from_stream(reader),
            head_pitch=await Byte.from_stream(reader), object_data=await VarInt.from_stream(reader),
            velocityx=await Short.from_stream(reader), velocityy=await Short.from_stream(reader),
            velocityz=await Short.from_stream(reader)
        )


class SpawnEntityExperienceOrbResponse(InboundEvent):
    packet_id = 0x02
    state = ConnectionState.PLAY

    def __init__(
        self,
        entity_id: VarInt, x: Double, y: Double, z: Double, count: Short,
    ) -> None:
        self.entity_id = entity_id
        self.x = x
        self.y = y
        self.z = z
        self.count = count

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'SpawnEntityExperienceOrbResponse':
        return cls(
            entity_id=await VarInt.from_stream(reader), x=await Double.from_stream(reader),
            y=await Double.from_stream(reader), z=await Double.from_stream(reader),
            count=await Short.from_stream(reader)
        )


class AnimationResponse(InboundEvent):
    packet_id = 0x03
    state = ConnectionState.PLAY

    def __init__(
        self,
        entity_id: VarInt, animation: UByte,
    ) -> None:
        self.entity_id = entity_id
        self.animation = animation

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'AnimationResponse':
        return cls(
            entity_id=await VarInt.from_stream(reader), animation=await UByte.from_stream(reader)
        )


class DifficultyResponse(InboundEvent):
    packet_id = 0x0b
    state = ConnectionState.PLAY

    def __init__(
        self,
        difficulty: UByte, difficulty_locked: Boolean,
    ) -> None:
        self.difficulty = difficulty
        self.difficulty_locked = difficulty_locked

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'DifficultyResponse':
        return cls(
            difficulty=await UByte.from_stream(reader), difficulty_locked=await Boolean.from_stream(reader)
        )


class ChunkBatchFinishedResponse(InboundEvent):
    packet_id = 0x0c
    state = ConnectionState.PLAY

    def __init__(
        self,
        batch_size: VarInt,
    ) -> None:
        self.batch_size = batch_size

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'ChunkBatchFinishedResponse':
        return cls(
            batch_size=await VarInt.from_stream(reader)
        )


class ChunkBatchStartResponse(InboundEvent):
    packet_id = 0x0d
    state = ConnectionState.PLAY


class CloseWindowResponse(InboundEvent):
    packet_id = 0x12
    state = ConnectionState.PLAY

    def __init__(
        self,
        window_id: UByte,
    ) -> None:
        self.window_id = window_id

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'CloseWindowResponse':
        return cls(
            window_id=await UByte.from_stream(reader)
        )


class CraftProgressBarResponse(InboundEvent):
    packet_id = 0x14
    state = ConnectionState.PLAY

    def __init__(
        self,
        window_id: UByte, property: Short, value: Short,
    ) -> None:
        self.window_id = window_id
        self.property = property
        self.value = value

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'CraftProgressBarResponse':
        return cls(
            window_id=await UByte.from_stream(reader), property=await Short.from_stream(reader),
            value=await Short.from_stream(reader)
        )


class SetCooldownResponse(InboundEvent):
    packet_id = 0x16
    state = ConnectionState.PLAY

    def __init__(
        self,
        itemid: VarInt, cooldown_ticks: VarInt,
    ) -> None:
        self.itemid = itemid
        self.cooldown_ticks = cooldown_ticks

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'SetCooldownResponse':
        return cls(
            itemid=await VarInt.from_stream(reader), cooldown_ticks=await VarInt.from_stream(reader)
        )


class EntityStatusResponse(InboundEvent):
    packet_id = 0x1d
    state = ConnectionState.PLAY

    def __init__(
        self,
        entity_id: Int, entity_status: Byte,
    ) -> None:
        self.entity_id = entity_id
        self.entity_status = entity_status

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'EntityStatusResponse':
        return cls(
            entity_id=await Int.from_stream(reader), entity_status=await Byte.from_stream(reader)
        )


class UnloadChunkResponse(InboundEvent):
    packet_id = 0x1f
    state = ConnectionState.PLAY

    def __init__(
        self,
        chunkz: Int, chunkx: Int,
    ) -> None:
        self.chunkz = chunkz
        self.chunkx = chunkx

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'UnloadChunkResponse':
        return cls(
            chunkz=await Int.from_stream(reader), chunkx=await Int.from_stream(reader)
        )


class DamageEventResponse(InboundEvent):
    packet_id = 0x19
    state = ConnectionState.PLAY

    def __init__(
        self,
        entity_id: VarInt,
        source_type_id: VarInt,
        source_cause_id: VarInt,
        source_direct_id: VarInt,
        has_source_position: Boolean,
        source_position_x: Optional[Double] = None,
        source_position_y: Optional[Double] = None,
        source_position_z: Optional[Double] = None,
    ) -> None:
        self.entity_id = entity_id
        self.source_type_id = source_type_id

        self.source_cause_id = source_cause_id
        if self.source_cause_id != 0:
            self.source_cause_id = VarInt(self.source_cause_id.int - 1)

        self.source_direct_id = source_direct_id
        if self.source_direct_id != 0:
            self.source_direct_id = VarInt(self.source_direct_id.int - 1)

        self.has_source_position = has_source_position
        self.source_position_x = source_position_x
        self.source_position_y = source_position_y
        self.source_position_z = source_position_z

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'DamageEventResponse':
        instance = cls(
            entity_id=await VarInt.from_stream(reader),
            source_type_id=await VarInt.from_stream(reader),
            source_cause_id=await VarInt.from_stream(reader),
            source_direct_id=await VarInt.from_stream(reader),
            has_source_position=await Boolean.from_stream(reader),
        )
        if instance.has_source_position:
            instance.source_position_x = await Double.from_stream(reader)
            instance.source_position_y = await Double.from_stream(reader)
            instance.source_position_z = await Double.from_stream(reader)
        return instance


class GameStateChangeResponse(InboundEvent):
    packet_id = 0x20
    state = ConnectionState.PLAY

    def __init__(
        self,
        reason: UByte, game_mode: Float,
    ) -> None:
        self.reason = reason
        self.game_mode = game_mode

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'GameStateChangeResponse':
        return cls(
            reason=await UByte.from_stream(reader), game_mode=await Float.from_stream(reader)
        )


class OpenHorseWindowResponse(InboundEvent):
    packet_id = 0x21
    state = ConnectionState.PLAY

    def __init__(
        self,
        window_id: UByte, nb_slots: VarInt, entity_id: Int,
    ) -> None:
        self.window_id = window_id
        self.nb_slots = nb_slots
        self.entity_id = entity_id

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'OpenHorseWindowResponse':
        return cls(
            window_id=await UByte.from_stream(reader), nb_slots=await VarInt.from_stream(reader),
            entity_id=await Int.from_stream(reader)
        )


class KeepAliveResponse(InboundEvent):
    packet_id = 0x24
    state = ConnectionState.PLAY

    def __init__(
        self,
        keep_alive_id: Long,
    ) -> None:
        self.keep_alive_id = keep_alive_id

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'KeepAliveResponse':
        return cls(
            keep_alive_id=await Long.from_stream(reader)
        )


class LoginResponse(InboundEvent):
    packet_id = 0x29
    state = ConnectionState.PLAY

    def __init__(
        self,
        entity_id: Int,
        is_hardcore: Boolean,
        dimension_count: VarInt,
        dimension_names: Array[String],
        max_players: VarInt,
        view_distance: VarInt,
        simulation_distance: VarInt,
        reduced_debug_info: Boolean,
        enable_respawn_screen: Boolean,
        do_limited_crafting: Boolean,
        dimension_type: String,
        dimension_name: String,
        hashed_seed: Long,
        game_mode: UByte,
        previous_game_mode: Byte,
        is_debug: Boolean,
        is_flat: Boolean,
        has_death_location: Boolean,
        portal_cooldown: VarInt,
        death_dimension_name: String | None = None,
        death_location: Position | None = None,
    ) -> None:
        self.entity_id = entity_id
        self.is_hardcore = is_hardcore
        self.dimension_count = dimension_count
        self.dimension_names = dimension_names
        self.max_players = max_players
        self.view_distance = view_distance
        self.simulation_distance = simulation_distance
        self.reduced_debug_info = reduced_debug_info
        self.enable_respawn_screen = enable_respawn_screen
        self.do_limited_crafting = do_limited_crafting
        self.dimension_type = dimension_type
        self.dimension_name = dimension_name
        self.hashed_seed = hashed_seed
        self.game_mode = game_mode
        self.previous_game_mode = previous_game_mode
        self.is_debug = is_debug
        self.is_flat = is_flat
        self.has_death_location = has_death_location
        self.portal_cooldown = portal_cooldown
        self.death_dimension_name = death_dimension_name
        self.death_location = death_location

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'LoginResponse':
        entity_id = await Int.from_stream(reader)
        is_hardcore = await Boolean.from_stream(reader)
        dimension_count = await VarInt.from_stream(reader)
        dimension_names = await Array.from_stream(reader, dimension_count.int, String)
        max_players = await VarInt.from_stream(reader)
        view_distance = await VarInt.from_stream(reader)
        simulation_distance = await VarInt.from_stream(reader)
        reduced_debug_info = await Boolean.from_stream(reader)
        enable_respawn_screen = await Boolean.from_stream(reader)
        do_limited_crafting = await Boolean.from_stream(reader)
        dimension_type = await String.from_stream(reader)
        dimension_name = await String.from_stream(reader)
        hashed_seed = await Long.from_stream(reader)
        game_mode = await UByte.from_stream(reader)
        previous_game_mode = await Byte.from_stream(reader)
        is_debug = await Boolean.from_stream(reader)
        is_flat = await Boolean.from_stream(reader)
        has_death_location = await Boolean.from_stream(reader)
        if has_death_location:
            death_dimension_name = await String.from_stream(reader)
            death_location = await Position.from_stream(reader)
        else:
            death_dimension_name = None
            death_location = None
        portal_cooldown = await VarInt.from_stream(reader)
        return cls(
            entity_id=entity_id, is_hardcore=is_hardcore, dimension_count=dimension_count,
            dimension_names=dimension_names, max_players=max_players, view_distance=view_distance,
            simulation_distance=simulation_distance, reduced_debug_info=reduced_debug_info,
            enable_respawn_screen=enable_respawn_screen, do_limited_crafting=do_limited_crafting,
            dimension_type=dimension_type, dimension_name=dimension_name, hashed_seed=hashed_seed,
            game_mode=game_mode, previous_game_mode=previous_game_mode, is_debug=is_debug, is_flat=is_flat,
            has_death_location=has_death_location, portal_cooldown=portal_cooldown,
            death_dimension_name=death_dimension_name, death_location=death_location
        )


class RelEntityMoveResponse(InboundEvent):
    packet_id = 0x2c
    state = ConnectionState.PLAY

    def __init__(
        self,
        entity_id: VarInt, dx: Short, dy: Short, dz: Short, on_ground: Boolean,
    ) -> None:
        self.entity_id = entity_id
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.on_ground = on_ground

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'RelEntityMoveResponse':
        return cls(
            entity_id=await VarInt.from_stream(reader), dx=await Short.from_stream(reader),
            dy=await Short.from_stream(reader), dz=await Short.from_stream(reader),
            on_ground=await Boolean.from_stream(reader)
        )


class EntityMoveLookResponse(InboundEvent):
    packet_id = 0x2d
    state = ConnectionState.PLAY

    def __init__(
        self,
        entity_id: VarInt, dx: Short, dy: Short, dz: Short, yaw: Byte, pitch: Byte, on_ground: Boolean,
    ) -> None:
        self.entity_id = entity_id
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.yaw = yaw
        self.pitch = pitch
        self.on_ground = on_ground

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'EntityMoveLookResponse':
        return cls(
            entity_id=await VarInt.from_stream(reader), dx=await Short.from_stream(reader),
            dy=await Short.from_stream(reader), dz=await Short.from_stream(reader), yaw=await Byte.from_stream(reader),
            pitch=await Byte.from_stream(reader), on_ground=await Boolean.from_stream(reader)
        )


class EntityLookResponse(InboundEvent):
    packet_id = 0x2e
    state = ConnectionState.PLAY

    def __init__(
        self,
        entity_id: VarInt, yaw: Byte, pitch: Byte, on_ground: Boolean,
    ) -> None:
        self.entity_id = entity_id
        self.yaw = yaw
        self.pitch = pitch
        self.on_ground = on_ground

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'EntityLookResponse':
        return cls(
            entity_id=await VarInt.from_stream(reader), yaw=await Byte.from_stream(reader),
            pitch=await Byte.from_stream(reader), on_ground=await Boolean.from_stream(reader)
        )


class VehicleMoveResponse(InboundEvent):
    packet_id = 0x2f
    state = ConnectionState.PLAY

    def __init__(
        self,
        x: Double, y: Double, z: Double, yaw: Float, pitch: Float,
    ) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.pitch = pitch

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'VehicleMoveResponse':
        return cls(
            x=await Double.from_stream(reader), y=await Double.from_stream(reader), z=await Double.from_stream(reader),
            yaw=await Float.from_stream(reader), pitch=await Float.from_stream(reader)
        )


class OpenBookResponse(InboundEvent):
    packet_id = 0x30
    state = ConnectionState.PLAY

    def __init__(
        self,
        hand: VarInt,
    ) -> None:
        self.hand = hand

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'OpenBookResponse':
        return cls(
            hand=await VarInt.from_stream(reader)
        )


class CraftRecipeResponse(InboundEvent):
    packet_id = 0x35
    state = ConnectionState.PLAY

    def __init__(
        self,
        window_id: Byte, recipe: String,
    ) -> None:
        self.window_id = window_id
        self.recipe = recipe

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'CraftRecipeResponse':
        return cls(
            window_id=await Byte.from_stream(reader), recipe=await String.from_stream(reader)
        )


class AbilitiesResponse(InboundEvent):
    packet_id = 0x36
    state = ConnectionState.PLAY

    def __init__(
        self,
        flags: Byte, flying_speed: Float, walking_speed: Float,
    ) -> None:
        self.flags = flags
        self.flying_speed = flying_speed
        self.walking_speed = walking_speed

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'AbilitiesResponse':
        return cls(
            flags=await Byte.from_stream(reader), flying_speed=await Float.from_stream(reader),
            walking_speed=await Float.from_stream(reader)
        )


class EndCombatEventResponse(InboundEvent):
    packet_id = 0x38
    state = ConnectionState.PLAY

    def __init__(
        self,
        duration: VarInt,
    ) -> None:
        self.duration = duration

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'EndCombatEventResponse':
        return cls(
            duration=await VarInt.from_stream(reader)
        )


class EnterCombatEventResponse(InboundEvent):
    packet_id = 0x39
    state = ConnectionState.PLAY


class CombatDeathResponse(InboundEvent):
    packet_id = 0x3A
    state = ConnectionState.PLAY

    def __init__(
        self,
        player_id: VarInt,
        message: String,
    ) -> None:
        self.player_id = player_id
        self.message = message

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'CombatDeathResponse':
        return cls(
            player_id=await VarInt.from_stream(reader),
            message=await String.from_stream(reader)
        )


class PositionResponse(InboundEvent):
    packet_id = 0x3e
    state = ConnectionState.PLAY

    def __init__(
        self,
        x: Double, y: Double, z: Double, yaw: Float, pitch: Float, flags: Byte, teleport_id: VarInt,
    ) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.pitch = pitch
        self.flags = flags
        self.teleport_id = teleport_id

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'PositionResponse':
        return cls(
            x=await Double.from_stream(reader), y=await Double.from_stream(reader), z=await Double.from_stream(reader),
            yaw=await Float.from_stream(reader), pitch=await Float.from_stream(reader),
            flags=await Byte.from_stream(reader), teleport_id=await VarInt.from_stream(reader)
        )


class RemoveEntityEffectResponse(InboundEvent):
    packet_id = 0x41
    state = ConnectionState.PLAY

    def __init__(
        self,
        entity_id: VarInt, effect_id: VarInt,
    ) -> None:
        self.entity_id = entity_id
        self.effect_id = effect_id

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'RemoveEntityEffectResponse':
        return cls(
            entity_id=await VarInt.from_stream(reader), effect_id=await VarInt.from_stream(reader)
        )


class ResetScoreResponse(InboundEvent):
    packet_id = 0x42
    state = ConnectionState.PLAY

    def __init__(
        self,
        entity_name: String, objective_name: String,
    ) -> None:
        self.entity_name = entity_name
        self.objective_name = objective_name

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'ResetScoreResponse':
        return cls(
            entity_name=await String.from_stream(reader), objective_name=await String.from_stream(reader)
        )


class RemoveResourcePackResponse(InboundEvent):
    packet_id = 0x43
    state = ConnectionState.PLAY

    def __init__(
        self,
        uuid: UUID,
    ) -> None:
        self.uuid = uuid

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'RemoveResourcePackResponse':
        return cls(
            uuid=await UUID.from_stream(reader)
        )


class EntityHeadRotationResponse(InboundEvent):
    packet_id = 0x46
    state = ConnectionState.PLAY

    def __init__(
        self,
        entity_id: VarInt, head_yaw: Byte,
    ) -> None:
        self.entity_id = entity_id
        self.head_yaw = head_yaw

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'EntityHeadRotationResponse':
        return cls(
            entity_id=await VarInt.from_stream(reader), head_yaw=await Byte.from_stream(reader)
        )


class CameraResponse(InboundEvent):
    packet_id = 0x50
    state = ConnectionState.PLAY

    def __init__(
        self,
        camera_id: VarInt,
    ) -> None:
        self.camera_id = camera_id

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'CameraResponse':
        return cls(
            camera_id=await VarInt.from_stream(reader)
        )


class HeldItemSlotResponse(InboundEvent):
    packet_id = 0x51
    state = ConnectionState.PLAY

    def __init__(
        self,
        slot: Byte,
    ) -> None:
        self.slot = slot

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'HeldItemSlotResponse':
        return cls(
            slot=await Byte.from_stream(reader)
        )


class UpdateViewPositionResponse(InboundEvent):
    packet_id = 0x52
    state = ConnectionState.PLAY

    def __init__(
        self,
        chunkx: VarInt, chunkz: VarInt,
    ) -> None:
        self.chunkx = chunkx
        self.chunkz = chunkz

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'UpdateViewPositionResponse':
        return cls(
            chunkx=await VarInt.from_stream(reader), chunkz=await VarInt.from_stream(reader)
        )


class UpdateViewDistanceResponse(InboundEvent):
    packet_id = 0x53
    state = ConnectionState.PLAY

    def __init__(
        self,
        view_distance: VarInt,
    ) -> None:
        self.view_distance = view_distance

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'UpdateViewDistanceResponse':
        return cls(
            view_distance=await VarInt.from_stream(reader)
        )


class ScoreboardDisplayObjectiveResponse(InboundEvent):
    packet_id = 0x55
    state = ConnectionState.PLAY

    def __init__(
        self,
        position: VarInt, name: String,
    ) -> None:
        self.position = position
        self.name = name

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'ScoreboardDisplayObjectiveResponse':
        return cls(
            position=await VarInt.from_stream(reader), name=await String.from_stream(reader)
        )


class AttachEntityResponse(InboundEvent):
    packet_id = 0x57
    state = ConnectionState.PLAY

    def __init__(
        self,
        entity_id: Int, vehicle_id: Int,
    ) -> None:
        self.entity_id = entity_id
        self.vehicle_id = vehicle_id

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'AttachEntityResponse':
        return cls(
            entity_id=await Int.from_stream(reader), vehicle_id=await Int.from_stream(reader)
        )


class EntityVelocityResponse(InboundEvent):
    packet_id = 0x58
    state = ConnectionState.PLAY

    def __init__(
        self,
        entity_id: VarInt, velocityx: Short, velocityy: Short, velocityz: Short,
    ) -> None:
        self.entity_id = entity_id
        self.velocityx = velocityx
        self.velocityy = velocityy
        self.velocityz = velocityz

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'EntityVelocityResponse':
        return cls(
            entity_id=await VarInt.from_stream(reader), velocityx=await Short.from_stream(reader),
            velocityy=await Short.from_stream(reader), velocityz=await Short.from_stream(reader)
        )


class ExperienceResponse(InboundEvent):
    packet_id = 0x5a
    state = ConnectionState.PLAY

    def __init__(
        self,
        experience_bar: Float, level: VarInt, total_experience: VarInt,
    ) -> None:
        self.experience_bar = experience_bar
        self.level = level
        self.total_experience = total_experience

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'ExperienceResponse':
        return cls(
            experience_bar=await Float.from_stream(reader), level=await VarInt.from_stream(reader),
            total_experience=await VarInt.from_stream(reader)
        )


class UpdateHealthResponse(InboundEvent):
    packet_id = 0x5b
    state = ConnectionState.PLAY

    def __init__(
        self,
        health: Float, food: VarInt, food_saturation: Float,
    ) -> None:
        self.health = health
        self.food = food
        self.food_saturation = food_saturation

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'UpdateHealthResponse':
        return cls(
            health=await Float.from_stream(reader), food=await VarInt.from_stream(reader),
            food_saturation=await Float.from_stream(reader)
        )


class UpdateTimeResponse(InboundEvent):
    packet_id = 0x62
    state = ConnectionState.PLAY

    def __init__(
        self,
        age: Long, time: Long,
    ) -> None:
        self.age = age
        self.time = time

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'UpdateTimeResponse':
        return cls(
            age=await Long.from_stream(reader), time=await Long.from_stream(reader)
        )


class SetDefaultSpawnPositionResponse(InboundEvent):
    packet_id = 0x54
    state = ConnectionState.PLAY

    def __init__(
        self,
        location: Position,
        angle: Float,
    ) -> None:
        self.location = location
        self.angle = angle

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'SetDefaultSpawnPositionResponse':
        return cls(
            location=await Position.from_stream(reader), angle=await Float.from_stream(reader)
        )


class CollectResponse(InboundEvent):
    packet_id = 0x6c
    state = ConnectionState.PLAY

    def __init__(
        self,
        collected_entity_id: VarInt, collector_entity_id: VarInt, pickup_item_count: VarInt,
    ) -> None:
        self.collected_entity_id = collected_entity_id
        self.collector_entity_id = collector_entity_id
        self.pickup_item_count = pickup_item_count

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'CollectResponse':
        return cls(
            collected_entity_id=await VarInt.from_stream(reader), collector_entity_id=await VarInt.from_stream(reader),
            pickup_item_count=await VarInt.from_stream(reader)
        )


class EntityTeleportResponse(InboundEvent):
    packet_id = 0x6d
    state = ConnectionState.PLAY

    def __init__(
        self,
        entity_id: VarInt, x: Double, y: Double, z: Double, yaw: Byte, pitch: Byte, on_ground: Boolean,
    ) -> None:
        self.entity_id = entity_id
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.pitch = pitch
        self.on_ground = on_ground

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'EntityTeleportResponse':
        return cls(
            entity_id=await VarInt.from_stream(reader), x=await Double.from_stream(reader),
            y=await Double.from_stream(reader), z=await Double.from_stream(reader), yaw=await Byte.from_stream(reader),
            pitch=await Byte.from_stream(reader), on_ground=await Boolean.from_stream(reader)
        )


class SelectAdvancementTabResponse(InboundEvent):
    packet_id = 0x48
    state = ConnectionState.PLAY

    def __init__(
        self,
        id: String,
    ) -> None:
        self.id = id

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'SelectAdvancementTabResponse':
        return cls(
            id=await String.from_stream(reader)
        )


class AcknowledgePlayerDiggingResponse(InboundEvent):
    packet_id = 0x05
    state = ConnectionState.PLAY

    def __init__(
        self,
        sequence_id: VarInt,
    ) -> None:
        self.sequence_id = sequence_id

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'AcknowledgePlayerDiggingResponse':
        return cls(
            sequence_id=await VarInt.from_stream(reader)
        )


class RemoveEntityResponse(InboundEvent):
    packet_id = 0x40
    state = ConnectionState.PLAY

    def __init__(
        self,
        count: VarInt,
        entity_ids: Array[VarInt],
    ) -> None:
        self.count = count
        self.entity_ids = entity_ids

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'RemoveEntityResponse':
        count = await VarInt.from_stream(reader)
        return cls(
            count=count,
            entity_ids=await Array[VarInt].from_stream(reader, count.int, VarInt)
        )


class ClearTitlesResponse(InboundEvent):
    packet_id = 0x0f
    state = ConnectionState.PLAY

    def __init__(
        self,
        reset: Boolean,
    ) -> None:
        self.reset = reset

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'ClearTitlesResponse':
        return cls(
            reset=await Boolean.from_stream(reader)
        )


class InitializeWorldBorderResponse(InboundEvent):
    packet_id = 0x23
    state = ConnectionState.PLAY

    def __init__(
        self,
        x: Double, z: Double, old_diameter: Double, new_diameter: Double, speed: VarInt,
        portal_teleport_boundary: VarInt, warning_blocks: VarInt, warning_time: VarInt,
    ) -> None:
        self.x = x
        self.z = z
        self.old_diameter = old_diameter
        self.new_diameter = new_diameter
        self.speed = speed
        self.portal_teleport_boundary = portal_teleport_boundary
        self.warning_blocks = warning_blocks
        self.warning_time = warning_time

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'InitializeWorldBorderResponse':
        return cls(
            x=await Double.from_stream(reader), z=await Double.from_stream(reader),
            old_diameter=await Double.from_stream(reader), new_diameter=await Double.from_stream(reader),
            speed=await VarInt.from_stream(reader), portal_teleport_boundary=await VarInt.from_stream(reader),
            warning_blocks=await VarInt.from_stream(reader), warning_time=await VarInt.from_stream(reader)
        )


class WorldBorderCenterResponse(InboundEvent):
    packet_id = 0x4b
    state = ConnectionState.PLAY

    def __init__(
        self,
        x: Double, z: Double,
    ) -> None:
        self.x = x
        self.z = z

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'WorldBorderCenterResponse':
        return cls(
            x=await Double.from_stream(reader), z=await Double.from_stream(reader)
        )


class WorldBorderLerpSizeResponse(InboundEvent):
    packet_id = 0x4c
    state = ConnectionState.PLAY

    def __init__(
        self,
        old_diameter: Double, new_diameter: Double, speed: VarInt,
    ) -> None:
        self.old_diameter = old_diameter
        self.new_diameter = new_diameter
        self.speed = speed

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'WorldBorderLerpSizeResponse':
        return cls(
            old_diameter=await Double.from_stream(reader), new_diameter=await Double.from_stream(reader),
            speed=await VarInt.from_stream(reader)
        )


class WorldBorderSizeResponse(InboundEvent):
    packet_id = 0x4d
    state = ConnectionState.PLAY

    def __init__(
        self,
        diameter: Double,
    ) -> None:
        self.diameter = diameter

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'WorldBorderSizeResponse':
        return cls(
            diameter=await Double.from_stream(reader)
        )


class WorldBorderWarningDelayResponse(InboundEvent):
    packet_id = 0x4e
    state = ConnectionState.PLAY

    def __init__(
        self,
        warning_time: VarInt,
    ) -> None:
        self.warning_time = warning_time

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'WorldBorderWarningDelayResponse':
        return cls(
            warning_time=await VarInt.from_stream(reader)
        )


class WorldBorderWarningReachResponse(InboundEvent):
    packet_id = 0x4f
    state = ConnectionState.PLAY

    def __init__(
        self,
        warning_blocks: VarInt,
    ) -> None:
        self.warning_blocks = warning_blocks

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'WorldBorderWarningReachResponse':
        return cls(
            warning_blocks=await VarInt.from_stream(reader)
        )


class PingResponse(InboundEvent):
    packet_id = 0x33
    state = ConnectionState.PLAY

    def __init__(
        self,
        id: Int,
    ) -> None:
        self.id = id

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'PingResponse':
        return cls(
            id=await Int.from_stream(reader)
        )


class PingResponse(InboundEvent):
    packet_id = 0x34
    state = ConnectionState.PLAY

    def __init__(
        self,
        id: Long,
    ) -> None:
        self.id = id

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'PingResponse':
        return cls(
            id=await Long.from_stream(reader)
        )


class SetTitleTimeResponse(InboundEvent):
    packet_id = 0x64
    state = ConnectionState.PLAY

    def __init__(
        self,
        fade_in: Int, stay: Int, fade_out: Int,
    ) -> None:
        self.fade_in = fade_in
        self.stay = stay
        self.fade_out = fade_out

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'SetTitleTimeResponse':
        return cls(
            fade_in=await Int.from_stream(reader), stay=await Int.from_stream(reader),
            fade_out=await Int.from_stream(reader)
        )


class SimulationDistanceResponse(InboundEvent):
    packet_id = 0x60
    state = ConnectionState.PLAY

    def __init__(
        self,
        distance: VarInt,
    ) -> None:
        self.distance = distance

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'SimulationDistanceResponse':
        return cls(
            distance=await VarInt.from_stream(reader)
        )


class HurtAnimationResponse(InboundEvent):
    packet_id = 0x22
    state = ConnectionState.PLAY

    def __init__(
        self,
        entity_id: VarInt, yaw: Float,
    ) -> None:
        self.entity_id = entity_id
        self.yaw = yaw

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'HurtAnimationResponse':
        return cls(
            entity_id=await VarInt.from_stream(reader), yaw=await Float.from_stream(reader)
        )


class StartConfigurationResponse(InboundEvent):
    packet_id = 0x67
    state = ConnectionState.PLAY


class SetTickingStateResponse(InboundEvent):
    packet_id = 0x6e
    state = ConnectionState.PLAY

    def __init__(
        self,
        tick_rate: Float, is_frozen: Boolean,
    ) -> None:
        self.tick_rate = tick_rate
        self.is_frozen = is_frozen

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'SetTickingStateResponse':
        return cls(
            tick_rate=await Float.from_stream(reader), is_frozen=await Boolean.from_stream(reader)
        )


class StepTickResponse(InboundEvent):
    packet_id = 0x6f
    state = ConnectionState.PLAY

    def __init__(
        self,
        tick_steps: VarInt,
    ) -> None:
        self.tick_steps = tick_steps

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'StepTickResponse':
        return cls(
            tick_steps=await VarInt.from_stream(reader)
        )


class ChunkDataAndLightResponse(InboundEvent):
    packet_id = 0x25
    state = ConnectionState.PLAY

    """
    Chunk X	Int	Chunk coordinate (block coordinate divided by 16, rounded down)
    Chunk Z	Int	Chunk coordinate (block coordinate divided by 16, rounded down)
    Heightmaps	NBT	See Chunk Format#Heightmaps structure
    Size	VarInt	Size of Data in bytes
    Data	Byte Array	See Chunk Format#Data structure
    Number of block entities	VarInt	Number of elements in the following array
    Block Entity	Packed XZ	Array	Unsigned Byte	The packed section coordinates are relative to the chunk they are in. Values 0-15 are valid.
    packed_xz = ((blockX & 15) << 4) | (blockZ & 15) // encode
    x = packed_xz >> 4, z = packed_xz & 15 // decode
    Y	Short	The height relative to the world
    Type	VarInt	The type of block entity
    Data	NBT	The block entity's data, without the X, Y, and Z values
    """

    def __init__(
        self,
        chunk_x: Int,
        chunk_z: Int,
        heightmaps: bytes,

    ) -> None:
        self.chunk_x = chunk_x
        self.chunk_z = chunk_z
        self.heightmaps = heightmaps

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'ChunkDataAndLightResponse':
        return cls(
            chunk_x=await Int.from_stream(reader),
            chunk_z=await Int.from_stream(reader),
            heightmaps=await reader.read(-1)
        )
