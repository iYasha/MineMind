from mc_protocol.states.enums import ConnectionState
from mc_protocol.states.events import OutboundEvent
from mc_protocol.mc_types import *

        
class TeleportConfirmRequest(OutboundEvent):
    packet_id = 0x00
    state = ConnectionState.PLAY

    def __init__(
        self,
        teleport_id: VarInt,
    ) -> None:
        self.teleport_id = teleport_id

    @property
    def payload(self) -> bytes:
        return self.teleport_id.bytes

        
class SetDifficultyRequest(OutboundEvent):
    packet_id = 0x02
    state = ConnectionState.PLAY

    def __init__(
        self,
        new_difficulty: UByte,
    ) -> None:
        self.new_difficulty = new_difficulty

    @property
    def payload(self) -> bytes:
        return self.new_difficulty.bytes

        
class MessageAcknowledgementRequest(OutboundEvent):
    packet_id = 0x03
    state = ConnectionState.PLAY

    def __init__(
        self,
        count: VarInt,
    ) -> None:
        self.count = count

    @property
    def payload(self) -> bytes:
        return self.count.bytes

        
class QueryEntityNbtRequest(OutboundEvent):
    packet_id = 0x12
    state = ConnectionState.PLAY

    def __init__(
        self,
        transaction_id: VarInt, entity_id: VarInt,
    ) -> None:
        self.transaction_id = transaction_id
        self.entity_id = entity_id

    @property
    def payload(self) -> bytes:
        return self.transaction_id.bytes + self.entity_id.bytes

        
class PickItemRequest(OutboundEvent):
    packet_id = 0x1d
    state = ConnectionState.PLAY

    def __init__(
        self,
        slot: VarInt,
    ) -> None:
        self.slot = slot

    @property
    def payload(self) -> bytes:
        return self.slot.bytes

        
class NameItemRequest(OutboundEvent):
    packet_id = 0x27
    state = ConnectionState.PLAY

    def __init__(
        self,
        name: String,
    ) -> None:
        self.name = name

    @property
    def payload(self) -> bytes:
        return self.name.bytes

        
class SelectTradeRequest(OutboundEvent):
    packet_id = 0x2a
    state = ConnectionState.PLAY

    def __init__(
        self,
        slot: VarInt,
    ) -> None:
        self.slot = slot

    @property
    def payload(self) -> bytes:
        return self.slot.bytes

        
class SetBeaconEffectRequest(OutboundEvent):
    packet_id = 0x2b
    state = ConnectionState.PLAY

    def __init__(
        self,
        primary_effect: VarInt, secondary_effect: VarInt,
    ) -> None:
        self.primary_effect = primary_effect
        self.secondary_effect = secondary_effect

    @property
    def payload(self) -> bytes:
        return self.primary_effect.bytes + self.secondary_effect.bytes

        
class UpdateCommandBlockMinecartRequest(OutboundEvent):
    packet_id = 0x2e
    state = ConnectionState.PLAY

    def __init__(
        self,
        entity_id: VarInt, command: String, track_output: Boolean,
    ) -> None:
        self.entity_id = entity_id
        self.command = command
        self.track_output = track_output

    @property
    def payload(self) -> bytes:
        return self.entity_id.bytes + self.command.bytes + self.track_output.bytes

        
class TabCompleteRequest(OutboundEvent):
    packet_id = 0x0a
    state = ConnectionState.PLAY

    def __init__(
        self,
        transaction_id: VarInt, text: String,
    ) -> None:
        self.transaction_id = transaction_id
        self.text = text

    @property
    def payload(self) -> bytes:
        return self.transaction_id.bytes + self.text.bytes

        
class ClientCommandRequest(OutboundEvent):
    packet_id = 0x08
    state = ConnectionState.PLAY

    def __init__(
        self,
        action_id: VarInt,
    ) -> None:
        self.action_id = action_id

    @property
    def payload(self) -> bytes:
        return self.action_id.bytes

        
class SettingsRequest(OutboundEvent):
    packet_id = 0x09
    state = ConnectionState.PLAY

    def __init__(
        self,
        locale: String, view_distance: Byte, chat_flags: VarInt, chat_colors: Boolean, skin_parts: UByte, main_hand: VarInt, enable_text_filtering: Boolean, enable_server_listing: Boolean,
    ) -> None:
        self.locale = locale
        self.view_distance = view_distance
        self.chat_flags = chat_flags
        self.chat_colors = chat_colors
        self.skin_parts = skin_parts
        self.main_hand = main_hand
        self.enable_text_filtering = enable_text_filtering
        self.enable_server_listing = enable_server_listing

    @property
    def payload(self) -> bytes:
        return self.locale.bytes + self.view_distance.bytes + self.chat_flags.bytes + self.chat_colors.bytes + self.skin_parts.bytes + self.main_hand.bytes + self.enable_text_filtering.bytes + self.enable_server_listing.bytes

        
class EnchantItemRequest(OutboundEvent):
    packet_id = 0x0c
    state = ConnectionState.PLAY

    def __init__(
        self,
        window_id: Byte, enchantment: Byte,
    ) -> None:
        self.window_id = window_id
        self.enchantment = enchantment

    @property
    def payload(self) -> bytes:
        return self.window_id.bytes + self.enchantment.bytes

        
class CloseWindowRequest(OutboundEvent):
    packet_id = 0x0e
    state = ConnectionState.PLAY

    def __init__(
        self,
        window_id: UByte,
    ) -> None:
        self.window_id = window_id

    @property
    def payload(self) -> bytes:
        return self.window_id.bytes

        
class KeepAliveRequest(OutboundEvent):
    packet_id = 0x15
    state = ConnectionState.PLAY

    def __init__(
        self,
        keep_alive_id: Long,
    ) -> None:
        self.keep_alive_id = keep_alive_id

    @property
    def payload(self) -> bytes:
        return self.keep_alive_id.bytes

        
class LockDifficultyRequest(OutboundEvent):
    packet_id = 0x16
    state = ConnectionState.PLAY

    def __init__(
        self,
        locked: Boolean,
    ) -> None:
        self.locked = locked

    @property
    def payload(self) -> bytes:
        return self.locked.bytes

        
class PositionRequest(OutboundEvent):
    packet_id = 0x17
    state = ConnectionState.PLAY

    def __init__(
        self,
        x: Double, y: Double, z: Double, on_ground: Boolean,
    ) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.on_ground = on_ground

    @property
    def payload(self) -> bytes:
        return self.x.bytes + self.y.bytes + self.z.bytes + self.on_ground.bytes

        
class PositionLookRequest(OutboundEvent):
    packet_id = 0x18
    state = ConnectionState.PLAY

    def __init__(
        self,
        x: Double, y: Double, z: Double, yaw: Float, pitch: Float, on_ground: Boolean,
    ) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.pitch = pitch
        self.on_ground = on_ground

    @property
    def payload(self) -> bytes:
        return self.x.bytes + self.y.bytes + self.z.bytes + self.yaw.bytes + self.pitch.bytes + self.on_ground.bytes

        
class LookRequest(OutboundEvent):
    packet_id = 0x19
    state = ConnectionState.PLAY

    def __init__(
        self,
        yaw: Float, pitch: Float, on_ground: Boolean,
    ) -> None:
        self.yaw = yaw
        self.pitch = pitch
        self.on_ground = on_ground

    @property
    def payload(self) -> bytes:
        return self.yaw.bytes + self.pitch.bytes + self.on_ground.bytes

        
class FlyingRequest(OutboundEvent):
    packet_id = 0x1a
    state = ConnectionState.PLAY

    def __init__(
        self,
        on_ground: Boolean,
    ) -> None:
        self.on_ground = on_ground

    @property
    def payload(self) -> bytes:
        return self.on_ground.bytes

        
class VehicleMoveRequest(OutboundEvent):
    packet_id = 0x1b
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

    @property
    def payload(self) -> bytes:
        return self.x.bytes + self.y.bytes + self.z.bytes + self.yaw.bytes + self.pitch.bytes

        
class SteerBoatRequest(OutboundEvent):
    packet_id = 0x1c
    state = ConnectionState.PLAY

    def __init__(
        self,
        left_paddle: Boolean, right_paddle: Boolean,
    ) -> None:
        self.left_paddle = left_paddle
        self.right_paddle = right_paddle

    @property
    def payload(self) -> bytes:
        return self.left_paddle.bytes + self.right_paddle.bytes

        
class CraftRecipeRequest(OutboundEvent):
    packet_id = 0x1f
    state = ConnectionState.PLAY

    def __init__(
        self,
        window_id: Byte, recipe: String, make_all: Boolean,
    ) -> None:
        self.window_id = window_id
        self.recipe = recipe
        self.make_all = make_all

    @property
    def payload(self) -> bytes:
        return self.window_id.bytes + self.recipe.bytes + self.make_all.bytes

        
class AbilitiesRequest(OutboundEvent):
    packet_id = 0x20
    state = ConnectionState.PLAY

    def __init__(
        self,
        flags: Byte,
    ) -> None:
        self.flags = flags

    @property
    def payload(self) -> bytes:
        return self.flags.bytes

        
class EntityActionRequest(OutboundEvent):
    packet_id = 0x22
    state = ConnectionState.PLAY

    def __init__(
        self,
        entity_id: VarInt, action_id: VarInt, jump_boost: VarInt,
    ) -> None:
        self.entity_id = entity_id
        self.action_id = action_id
        self.jump_boost = jump_boost

    @property
    def payload(self) -> bytes:
        return self.entity_id.bytes + self.action_id.bytes + self.jump_boost.bytes

        
class SteerVehicleRequest(OutboundEvent):
    packet_id = 0x23
    state = ConnectionState.PLAY

    def __init__(
        self,
        sideways: Float, forward: Float, jump: UByte,
    ) -> None:
        self.sideways = sideways
        self.forward = forward
        self.jump = jump

    @property
    def payload(self) -> bytes:
        return self.sideways.bytes + self.forward.bytes + self.jump.bytes

        
class DisplayedRecipeRequest(OutboundEvent):
    packet_id = 0x26
    state = ConnectionState.PLAY

    def __init__(
        self,
        recipe_id: String,
    ) -> None:
        self.recipe_id = recipe_id

    @property
    def payload(self) -> bytes:
        return self.recipe_id.bytes

        
class RecipeBookRequest(OutboundEvent):
    packet_id = 0x25
    state = ConnectionState.PLAY

    def __init__(
        self,
        book_id: VarInt, book_open: Boolean, filter_active: Boolean,
    ) -> None:
        self.book_id = book_id
        self.book_open = book_open
        self.filter_active = filter_active

    @property
    def payload(self) -> bytes:
        return self.book_id.bytes + self.book_open.bytes + self.filter_active.bytes

        
class ResourcePackReceiveRequest(OutboundEvent):
    packet_id = 0x28
    state = ConnectionState.PLAY

    def __init__(
        self,
        uuid: UUID, result: VarInt,
    ) -> None:
        self.uuid = uuid
        self.result = result

    @property
    def payload(self) -> bytes:
        return self.uuid.bytes + self.result.bytes

        
class HeldItemSlotRequest(OutboundEvent):
    packet_id = 0x2c
    state = ConnectionState.PLAY

    def __init__(
        self,
        slot_id: Short,
    ) -> None:
        self.slot_id = slot_id

    @property
    def payload(self) -> bytes:
        return self.slot_id.bytes

        
class ArmAnimationRequest(OutboundEvent):
    packet_id = 0x33
    state = ConnectionState.PLAY

    def __init__(
        self,
        hand: VarInt,
    ) -> None:
        self.hand = hand

    @property
    def payload(self) -> bytes:
        return self.hand.bytes

        
class SpectateRequest(OutboundEvent):
    packet_id = 0x34
    state = ConnectionState.PLAY

    def __init__(
        self,
        target: UUID,
    ) -> None:
        self.target = target

    @property
    def payload(self) -> bytes:
        return self.target.bytes

        
class UseItemRequest(OutboundEvent):
    packet_id = 0x36
    state = ConnectionState.PLAY

    def __init__(
        self,
        hand: VarInt, sequence: VarInt,
    ) -> None:
        self.hand = hand
        self.sequence = sequence

    @property
    def payload(self) -> bytes:
        return self.hand.bytes + self.sequence.bytes

        
class PongRequest(OutboundEvent):
    packet_id = 0x24
    state = ConnectionState.PLAY

    def __init__(
        self,
        id: Int,
    ) -> None:
        self.id = id

    @property
    def payload(self) -> bytes:
        return self.id.bytes

        
class ChunkBatchReceivedRequest(OutboundEvent):
    packet_id = 0x07
    state = ConnectionState.PLAY

    def __init__(
        self,
        chunks_per_tick: Float,
    ) -> None:
        self.chunks_per_tick = chunks_per_tick

    @property
    def payload(self) -> bytes:
        return self.chunks_per_tick.bytes

        
class ConfigurationAcknowledgedRequest(OutboundEvent):
    packet_id = 0x0b
    state = ConnectionState.PLAY

            
class PingRequest(OutboundEvent):
    packet_id = 0x1e
    state = ConnectionState.PLAY

    def __init__(
        self,
        id: Long,
    ) -> None:
        self.id = id

    @property
    def payload(self) -> bytes:
        return self.id.bytes

        
class SetSlotStateRequest(OutboundEvent):
    packet_id = 0x0f
    state = ConnectionState.PLAY

    def __init__(
        self,
        slot_id: VarInt, window_id: VarInt, state: Boolean,
    ) -> None:
        self.slot_id = slot_id
        self.window_id = window_id
        self.state = state

    @property
    def payload(self) -> bytes:
        return self.slot_id.bytes + self.window_id.bytes + self.state.bytes

        