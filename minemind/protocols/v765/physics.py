import asyncio
import math
import time
import typing

from minemind import DEBUG_PROTOCOL
from minemind.client import Client
from minemind.dispatcher import EventDispatcher
from minemind.mc_types import Boolean, Double
from minemind.mc_types.base import Vector3
from minemind.protocols.base import InteractionModule
from minemind.protocols.utils import get_logger
from minemind.protocols.v765.constants import (
    AIR_BLOCK_ID,
    BUBBLE_COLUMN_ID,
    COB_WEB_ID,
    LAVA_BLOCK_ID,
    SLIME_BLOCK_ID,
    WATER_BLOCK_ID,
    WATER_LIKE_BLOCK_IDS,
)
from minemind.protocols.v765.inbound.play import LoginResponse, PositionResponse
from minemind.protocols.v765.outbound.play import PositionRequest
from minemind.protocols.v765.world import Block, World

if typing.TYPE_CHECKING:
    from minemind.protocols.v765.bot import Bot


class AABB:
    """Axis-Aligned Bounding Box"""

    def __init__(self, min_x: float, min_y: float, min_z: float, max_x: float, max_y: float, max_z: float):
        # TODO: Maybe it's better to use Decimal instead of float to get more accurate results
        self.min_x = min_x
        self.min_y = min_y
        self.min_z = min_z
        self.max_x = max_x
        self.max_y = max_y
        self.max_z = max_z

    def __repr__(self):
        return f'<AABB {self.min_x=} {self.min_y=} {self.min_z=} {self.max_x=} {self.max_y=} {self.max_z=}>'

    def copy(self) -> 'AABB':
        return AABB(self.min_x, self.min_y, self.min_z, self.max_x, self.max_y, self.max_z)

    def floor(self):
        self.min_x = math.floor(self.min_x)
        self.min_y = math.floor(self.min_y)
        self.min_z = math.floor(self.min_z)
        self.max_x = math.floor(self.max_x)
        self.max_y = math.floor(self.max_y)
        self.max_z = math.floor(self.max_z)
        return self

    def extend(self, dx: float, dy: float, dz: float):
        if dx < 0:
            self.min_x += dx
        else:
            self.max_x += dx

        if dy < 0:
            self.min_y += dy
        else:
            self.max_y += dy

        if dz < 0:
            self.min_z += dz
        else:
            self.max_z += dz
        return self

    def contract(self, dx: float, dy: float, dz: float):
        self.min_x += dx
        self.min_y += dy
        self.min_z += dz
        self.max_x -= dx
        self.max_y -= dy
        self.max_z -= dz
        return self

    def expand(self, dx: float, dy: float, dz: float):
        self.min_x -= dx
        self.min_y -= dy
        self.min_z -= dz
        self.max_x += dx
        self.max_y += dy
        self.max_z += dz
        return self

    def offset(self, dx: float, dy: float, dz: float):
        self.min_x += dx
        self.min_y += dy
        self.min_z += dz
        self.max_x += dx
        self.max_y += dy
        self.max_z += dz
        return self

    def get_offset_x(self, other: 'AABB', offset_x: float):
        if (
            other.max_y > self.min_y
            and other.min_y < self.max_y
            and other.max_z > self.min_z
            and other.min_z < self.max_z
        ):
            if offset_x > 0 and other.max_x <= self.min_x:
                return min(self.min_x - other.max_x, offset_x)
            elif offset_x < 0 and other.min_x >= self.max_x:
                return max(self.max_x - other.min_x, offset_x)
        return offset_x

    def get_offset_y(self, other: 'AABB', offset_y: float):
        if (
            other.max_x > self.min_x
            and other.min_x < self.max_x
            and other.max_z > self.min_z
            and other.min_z < self.max_z
        ):
            if offset_y > 0 and other.max_y <= self.min_y:
                return min(self.min_y - other.max_y, offset_y)
            elif offset_y < 0 and other.min_y >= self.max_y:
                return max(self.max_y - other.min_y, offset_y)
        return offset_y

    def get_offset_z(self, other: 'AABB', offset_z: float):
        if (
            other.max_x > self.min_x
            and other.min_x < self.max_x
            and other.max_y > self.min_y
            and other.min_y < self.max_y
        ):
            if offset_z > 0 and other.max_z <= self.min_z:
                return min(self.min_z - other.max_z, offset_z)
            elif offset_z < 0 and other.min_z >= self.max_z:
                return max(self.max_z - other.min_z, offset_z)
        return offset_z

    def intersects(self, other: 'AABB') -> bool:
        return (
            self.min_x < other.max_x
            and self.max_x > other.min_x
            and self.min_y < other.max_y
            and self.max_y > other.min_y
            and self.min_z < other.max_z
            and self.max_z > other.min_z
        )


def time_ms() -> int:
    """
    Get current time in milliseconds
    """
    return time.perf_counter_ns() // 1_000_000


class PlayerPhysicsSimulation:
    logger = get_logger('PlayerPhysicsSimulation')
    GRAVITY = 0.08
    SLOW_FALLING = 0.125
    AIRDRAG = 0.9800000190734863  # math.fround(1 - 0.02)
    PLAYER_HALF_WIDTH = 0.3
    PLAYER_HEIGHT = 1.8
    NEGLIGIBLE_VELOCITY = 0.003  # TODO: actually 0.005 for 1.8, but need to check
    LIQUID_ACCELERATION = 0.02
    OUT_OF_LIQUID_IMPULSE = 0.3
    STEP_HEIGHT = 0.6

    WATER_INERTIA = 0.8
    WATER_GRAVITY = 0.005

    LAVA_INERTIA = 0.5
    LAVA_GRAVITY = 0.02

    DEFAULT_SLIPPERINESS = 0.6
    AIRBORNE_INERTIA = 0.91
    AIRBORNE_ACCELERATION = 0.02

    BUBBLE_COLUMN_SURFACE_DRAG = {
        'down': 0.03,
        'max_down': -0.9,
        'up': 0.1,
        'max_up': 1.8,
    }
    BUBBLE_COLUMN_DRAG = {
        'down': 0.03,
        'max_down': -0.3,
        'up': 0.06,
        'max_up': 0.7,
    }

    def __init__(
        self,
        world: World,
        position: Vector3,
        velocity: Vector3,
        yaw: float,
        pitch: float,
        on_ground: bool,
        jump_ticks: int,
        is_in_web: bool,
        is_elytra_flying: bool,
        is_collided_horizontally: bool,
        is_collided_vertically: bool,
    ):
        self.world = world
        self.position = position
        self.velocity = velocity
        self.yaw = yaw
        self.pitch = pitch
        self.on_ground = on_ground
        self.jump_ticks = jump_ticks
        self.is_in_web = is_in_web
        self.is_elytra_flying = is_elytra_flying
        self.is_collided_horizontally = is_collided_horizontally
        self.is_collided_vertically = is_collided_vertically

        self.is_in_water = False
        self.apply_water_physics()

        self.is_in_lava = self.is_lava_physics_applied()

        # TODO: also need to check effects on player, is boots enchanted with depth strider, has elytra, etc.
        self.slow_falling = 0
        self.depth_strider = 0
        self.levitation = 0
        self.dolphins_grace = 0

    @classmethod
    def get_player_bb(cls, position: Vector3) -> AABB:
        w = cls.PLAYER_HALF_WIDTH
        return AABB(-w, 0, -w, w, cls.PLAYER_HEIGHT, w).offset(
            position.x,
            position.y,
            position.z,
        )

    def get_surrounding_bbs(self, query_bb: AABB):
        surrounding_bbs = []

        for y in range(math.floor(query_bb.min_y) - 1, math.floor(query_bb.max_y) + 1):
            for z in range(math.floor(query_bb.min_z), math.floor(query_bb.max_z) + 1):
                for x in range(math.floor(query_bb.min_x), math.floor(query_bb.max_x) + 1):
                    block = self.world.get_block_at(Vector3(x, y, z))
                    if block is None:
                        self.logger.log(DEBUG_PROTOCOL, 'Block is not set')
                        continue
                    if block.position is None:
                        self.logger.log(DEBUG_PROTOCOL, 'Block position is not set')
                        continue
                    for shape in block.get_shapes():
                        surrounding_bbs.append(
                            AABB(*shape).offset(block.position.x, block.position.y, block.position.z),
                        )
        return surrounding_bbs

    # -------- [START] WATER --------

    @classmethod
    def get_rendered_depth(cls, block: Block | None) -> int:
        if block is None:
            return -1
        if block.block_id in WATER_LIKE_BLOCK_IDS:
            return 0
        if bool(block.get_state('waterlogged')):
            return 0
        if block.block_id != WATER_BLOCK_ID:
            return -1

        level = block.state_id - block.min_state_id
        return 0 if level >= 8 else level

    @classmethod
    def get_liquid_height_percentage(cls, block: Block | None) -> float:
        return (cls.get_rendered_depth(block) + 1) / 9

    def get_water_blocks(self, water_bb: AABB) -> list[Block]:
        water_blocks: list[Block] = []
        for y in range(math.floor(water_bb.min_y), math.floor(water_bb.max_y) + 1):
            for z in range(math.floor(water_bb.min_z), math.floor(water_bb.max_z) + 1):
                for x in range(math.floor(water_bb.min_x), math.floor(water_bb.max_x) + 1):
                    block = self.world.get_block_at(Vector3(x, y, z))
                    if block is not None and (
                        WATER_BLOCK_ID == block.block_id
                        or block.block_id in WATER_LIKE_BLOCK_IDS
                        or bool(block.get_state('waterlogged'))
                    ):
                        water_level = y + 1 - self.get_liquid_height_percentage(block)
                        if math.ceil(water_bb.max_y) >= water_level:
                            water_blocks.append(block)
        return water_blocks

    def get_water_flow(self, block: Block) -> Vector3:
        current_level = self.get_rendered_depth(block)
        flow = Vector3(0, 0, 0)
        if block.position is None:
            raise ValueError('Block position is not set')
        for dx, dz in [[0, 1], [-1, 0], [0, -1], [1, 0]]:
            adjust_block = self.world.get_block_at(block.position.offset(dx, 0, dz))
            adjust_level = self.get_rendered_depth(adjust_block)
            if adjust_level < 0:
                if adjust_block is not None and adjust_block.bounding_box != 'empty':
                    adjust_level = self.get_rendered_depth(
                        self.world.get_block_at(block.position.offset(dx, -1, dz)),
                    )
                    if adjust_level >= 0:
                        flow_multiplier = adjust_level - (current_level - 8)
                        flow.x += dx * flow_multiplier
                        flow.z += dz * flow_multiplier
            else:
                flow_multiplier = adjust_level - current_level
                flow.x += dx * flow_multiplier
                flow.z += dz * flow_multiplier

        level = block.state_id - block.min_state_id
        if level >= 8:
            for dx, dz in [[0, 1], [-1, 0], [0, -1], [1, 0]]:
                adjust_block = self.world.get_block_at(block.position.offset(dx, 0, dz))
                adjust_above_block = self.world.get_block_at(block.position.offset(dx, 1, dz))
                if (adjust_block is not None and adjust_block.bounding_box != 'empty') or (
                    adjust_above_block is not None and adjust_above_block.bounding_box != 'empty'
                ):
                    flow.normalize().translate(0, -6, 0)

        return flow.normalize()

    def apply_water_physics(self) -> None:
        acceleration = Vector3(0, 0, 0)
        water_blocks = self.get_water_blocks(water_bb=self.get_player_bb(self.position).contract(0.001, 0.401, 0.001))
        self.is_in_water = len(water_blocks) > 0
        for block in water_blocks:
            flow = self.get_water_flow(block)
            acceleration.add(flow, inplace=True)

        length = acceleration.norm()
        if length > 0:
            self.velocity.x += acceleration.x / length * 0.014
            self.velocity.y += acceleration.y / length * 0.014
            self.velocity.z += acceleration.z / length * 0.014

    # -------- [END] WATER --------

    # -------- [START] LAVA --------

    def is_lava_physics_applied(self) -> bool:
        lava_bb = self.get_player_bb(self.position).contract(0.1, 0.4, 0.1)
        for y in range(math.floor(lava_bb.min_y), math.floor(lava_bb.max_y) + 1):
            for z in range(math.floor(lava_bb.min_z), math.floor(lava_bb.max_z) + 1):
                for x in range(math.floor(lava_bb.min_x), math.floor(lava_bb.max_x) + 1):
                    block = self.world.get_block_at(Vector3(x, y, z))
                    if block is not None and block.block_id == LAVA_BLOCK_ID:
                        return True
        return False

    # -------- [END] LAVA --------

    def set_position_to_bb(self, player_bb: AABB):
        self.position.x = player_bb.min_x + self.PLAYER_HALF_WIDTH
        self.position.y = player_bb.min_y
        self.position.z = player_bb.min_z + self.PLAYER_HALF_WIDTH

    def move_entity(self):
        dx = self.velocity.x
        dy = self.velocity.y
        dz = self.velocity.z
        if self.is_in_web:
            dx *= 0.25
            dy *= 0.05
            dz *= 0.25
            self.velocity.x = 0
            self.velocity.y = 0
            self.velocity.z = 0
            self.is_in_web = False

        old_vel_x = dx
        old_vel_y = dy
        old_vel_z = dz

        # TODO: Implement if sneaking and on_ground
        player_bb = self.get_player_bb(self.position)
        query_bb = player_bb.copy().extend(dx, dy, dz)
        surrounding_bbs = self.get_surrounding_bbs(query_bb)
        old_player_bb = player_bb.copy()

        for block_bb in surrounding_bbs:
            dy = block_bb.get_offset_y(player_bb, dy)
        player_bb.offset(0, dy, 0)

        for block_bb in surrounding_bbs:
            dx = block_bb.get_offset_x(player_bb, dx)
        player_bb.offset(dx, 0, 0)

        for block_bb in surrounding_bbs:
            dz = block_bb.get_offset_z(player_bb, dz)
        player_bb.offset(0, 0, dz)

        if (
            self.STEP_HEIGHT > 0
            and (self.on_ground or (dy != old_vel_y and old_vel_y < 0))
            and (dx != old_vel_x or dz != old_vel_z)
        ):
            old_vel_x_col = dx
            old_vel_y_col = dy
            old_vel_z_col = dz
            old_bb_col = player_bb.copy()

            dy = self.STEP_HEIGHT
            query_bb = old_player_bb.copy().extend(old_vel_x, dy, old_vel_z)
            surrounding_bbs = self.get_surrounding_bbs(query_bb)

            bb1 = old_player_bb.copy()
            bb2 = old_player_bb.copy()
            bb_xz = bb1.copy().extend(dx, 0, dz)

            dy1 = dy
            dy2 = dy

            for block_bb in surrounding_bbs:
                dy1 = block_bb.get_offset_y(bb_xz, dy1)
                dy2 = block_bb.get_offset_y(bb2, dy2)
            bb1.offset(0, dy1, 0)
            bb2.offset(0, dy2, 0)

            dx1 = old_vel_x
            dx2 = old_vel_x
            for block_bb in surrounding_bbs:
                dx1 = block_bb.get_offset_x(bb1, dx1)
                dx2 = block_bb.get_offset_x(bb2, dx2)
            bb1.offset(dx1, 0, 0)
            bb2.offset(dx2, 0, 0)

            dz1 = old_vel_z
            dz2 = old_vel_z
            for block_bb in surrounding_bbs:
                dz1 = block_bb.get_offset_z(bb1, dz1)
                dz2 = block_bb.get_offset_z(bb2, dz2)
            bb1.offset(0, 0, dz1)
            bb2.offset(0, 0, dz2)

            norm1 = dx1**2 + dz1**2
            norm2 = dx2**2 + dz2**2

            if norm1 > norm2:
                dx = dx1
                dy = -dy1
                dz = dz1
                player_bb = bb1
            else:
                dx = dx2
                dy = -dy2
                dz = dz2
                player_bb = bb2

            for block_bb in surrounding_bbs:
                dy = block_bb.get_offset_y(player_bb, dy)
            player_bb.offset(0, dy, 0)

            if old_vel_x_col**2 + old_vel_z_col**2 >= dx**2 + dz**2:
                dx = old_vel_x_col
                dy = old_vel_y_col
                dz = old_vel_z_col
                player_bb = old_bb_col

        self.set_position_to_bb(player_bb)
        self.is_collided_horizontally = dx != old_vel_x or dz != old_vel_z
        self.is_collided_vertically = dy != old_vel_y
        self.on_ground = self.is_collided_vertically and old_vel_y < 0

        block_at_feet = self.world.get_block_at(self.position.offset(0, -0.2, 0))

        if dx != old_vel_x:
            self.velocity.x = 0
        if dz != old_vel_z:
            self.velocity.z = 0
        if dy != old_vel_y:
            if block_at_feet and block_at_feet.block_id == SLIME_BLOCK_ID and True:  # TODO: If not sneaking
                self.velocity.y = -self.velocity.y
            else:
                self.velocity.y = 0

        player_bb.contract(0.001, 0.001, 0.001)
        for y in range(math.floor(player_bb.min_y), math.floor(player_bb.max_y) + 1):
            for z in range(math.floor(player_bb.min_z), math.floor(player_bb.max_z) + 1):
                for x in range(math.floor(player_bb.min_x), math.floor(player_bb.max_x) + 1):
                    block = self.world.get_block_at(Vector3(x, y, z))
                    if not block:
                        continue
                    if block.block_id == COB_WEB_ID:
                        self.is_in_web = True
                    if block.block_id == BUBBLE_COLUMN_ID:
                        down = not (block.state_id - block.min_state_id)
                        above_block = self.world.get_block_at(Vector3(x, y + 1, z))
                        bubble_drag = (
                            self.BUBBLE_COLUMN_SURFACE_DRAG
                            if above_block is not None and above_block.block_id == AIR_BLOCK_ID
                            else self.BUBBLE_COLUMN_DRAG
                        )
                        if down:
                            self.velocity.y = max(bubble_drag['max_down'], self.velocity.y - bubble_drag['down'])
                        else:
                            self.velocity.y = min(bubble_drag['max_up'], self.velocity.y + bubble_drag['up'])

    def apply_heading(self, strafe: float, forward: float, multiplier: float) -> None:
        speed = math.sqrt(strafe**2 + forward**2)
        if speed < 0.01:
            return

        speed = multiplier / max(speed, 1)

        strafe *= speed
        forward *= speed

        yaw = math.pi - self.yaw
        sin = math.sin(yaw)
        cos = math.cos(yaw)

        self.velocity.x -= strafe * cos + forward * sin
        self.velocity.z += forward * cos - strafe * sin

    def does_not_collide(self, position: Vector3) -> bool:
        p_bb = self.get_player_bb(position)
        return (
            not any(p_bb.intersects(x) for x in self.get_surrounding_bbs(p_bb))
            and len(self.get_water_blocks(p_bb)) == 0
        )

    def move_entity_with_heading(self, strafe: float, forward: float):
        gravity_multiplier = self.SLOW_FALLING if (self.velocity.y <= 0 < self.slow_falling) else 1

        if self.is_in_water or self.is_in_lava:
            last_y = self.position.y
            acceleration = self.LIQUID_ACCELERATION
            inertia = self.WATER_INERTIA if self.is_in_water else self.LAVA_INERTIA
            horizontal_inertia = inertia

            if self.is_in_water:
                strider = float(min(self.depth_strider, 3))
                if not self.on_ground:
                    strider *= 0.5
                if strider > 0:
                    horizontal_inertia += (0.546 - horizontal_inertia) * strider / 3
                    acceleration += (0.07 - acceleration) * strider / 3
                if self.dolphins_grace > 0:
                    horizontal_inertia = 0.96

            self.apply_heading(strafe, forward, acceleration)
            self.move_entity()
            self.velocity.y *= inertia
            self.velocity.y -= (self.WATER_GRAVITY if self.is_in_water else self.LAVA_GRAVITY) * gravity_multiplier
            self.velocity.x *= horizontal_inertia
            self.velocity.z *= horizontal_inertia

            if self.is_collided_horizontally and self.does_not_collide(
                self.position.offset(
                    self.velocity.x,
                    self.velocity.y + 0.6 - self.position.y + last_y,
                    self.velocity.z,
                ),
            ):
                self.velocity.y = self.OUT_OF_LIQUID_IMPULSE
        elif False:
            """elytra flying"""
        else:  # normal movement
            acceleration = 0.0
            inertia = 0.0
            block_under = self.world.get_block_at(self.position.offset(0, -1, 0))
            if self.on_ground and block_under:
                """TODO: Implement movement on ground"""
                attribute_speed = 0.1
                # inertia = (blockSlipperiness[blockUnder.type] or physics.defaultSlipperiness) * 0.91
                inertia = self.DEFAULT_SLIPPERINESS * 0.91
                acceleration = attribute_speed * (0.1627714 / (inertia**3))
                if acceleration < 0:
                    acceleration = 0
            else:
                acceleration = self.AIRBORNE_ACCELERATION
                inertia = self.AIRBORNE_INERTIA

            self.apply_heading(strafe, forward, acceleration)

            if False:  # is_on_ladder
                pass

            self.move_entity()

            if self.levitation > 0:
                self.velocity.y += (0.05 * self.levitation - self.velocity.y) * 0.2
            else:
                self.velocity.y -= self.GRAVITY * gravity_multiplier

            self.velocity.y *= self.AIRDRAG
            self.velocity.x *= inertia
            self.velocity.z *= inertia

    def simulate(self):
        if abs(self.velocity.x) < self.NEGLIGIBLE_VELOCITY:
            self.velocity.x = 0
        if abs(self.velocity.y) < self.NEGLIGIBLE_VELOCITY:
            self.velocity.y = 0
        if abs(self.velocity.z) < self.NEGLIGIBLE_VELOCITY:
            self.velocity.z = 0

        if False:
            pass  # TODO: handle inputs later
        else:
            self.jump_ticks = 0

        # right - left
        strafe = (False - False) * 0.98

        # forward - back
        forward = (False - False) * 0.98

        self.move_entity_with_heading(strafe, forward)


class Physics(InteractionModule):
    logger = get_logger('Physics')
    PHYSICS_INTERVAL_MS = 50
    PHYSICS_TIME_STEP = PHYSICS_INTERVAL_MS / 1000  # 0.05

    def __init__(self, client: Client, bot: 'Bot'):
        self.client = client
        self.bot = bot
        self.use_physics = False
        self.time_accumulator = 0
        self.catchup_ticks = 0
        self.max_catchup_ticks = 4
        self.last_frame_time = time_ms()
        self.timer_task: asyncio.Task | None = None

        self.jump_ticks = 0
        self.is_in_web = False
        self.is_elytra_flying = False
        self.is_collided_horizontally = False
        self.is_collided_vertically = False

    def __del__(self):
        if self.timer_task is not None:
            self.timer_task.cancel()

    async def on_tick(self, now: int):
        if self.bot.entity is None:
            self.logger.log(DEBUG_PROTOCOL, 'Player entity is not set')
            return
        if self.bot.world.get_block_at(self.bot.entity.position) is None:
            self.logger.log(DEBUG_PROTOCOL, 'Waiting for chunk to load')
            return
        simulation = PlayerPhysicsSimulation(
            world=self.bot.world,
            position=self.bot.entity.position.copy(),
            velocity=self.bot.entity.velocity.copy(),
            yaw=self.bot.entity.yaw,
            pitch=self.bot.entity.pitch,
            on_ground=self.bot.entity.on_ground,
            jump_ticks=self.jump_ticks,
            # TODO: Store these values somewhere, maybe in the entity class?
            is_in_web=self.is_in_web,
            is_elytra_flying=self.is_elytra_flying,
            is_collided_horizontally=self.is_collided_horizontally,
            is_collided_vertically=self.is_collided_vertically,
        )
        simulation.simulate()
        self.bot.entity.position = simulation.position
        self.bot.entity.velocity = simulation.velocity
        self.bot.entity.yaw = simulation.yaw
        self.bot.entity.pitch = simulation.pitch
        self.bot.entity.on_ground = simulation.on_ground
        self.jump_ticks = simulation.jump_ticks
        self.is_in_web = simulation.is_in_web
        self.is_elytra_flying = simulation.is_elytra_flying
        self.is_collided_horizontally = simulation.is_collided_horizontally
        self.is_collided_vertically = simulation.is_collided_vertically
        await self.client.send_packet(
            PositionRequest(
                x=Double(simulation.position.x),
                y=Double(simulation.position.y),
                z=Double(simulation.position.z),
                on_ground=Boolean(simulation.on_ground),
            ),
        )
        # self.logger.log(DEBUG_GAME_EVENTS, f'Physics moved player to {simulation.position=}')

    async def timer(self):
        while True:
            try:
                now = time_ms()
                delta_seconds = (now - self.last_frame_time) / 1000
                self.last_frame_time = now
                self.time_accumulator += delta_seconds
                self.catchup_ticks = 0
                while self.time_accumulator >= self.PHYSICS_TIME_STEP:
                    if self.use_physics:
                        await self.on_tick(now)
                    self.time_accumulator -= self.PHYSICS_TIME_STEP
                    self.catchup_ticks += 1
                    if self.catchup_ticks >= self.max_catchup_ticks:
                        break
                await asyncio.sleep(self.PHYSICS_INTERVAL_MS / 1000)
            except Exception as e:
                print(e)

    @EventDispatcher.subscribe(LoginResponse)
    async def _start_playing(self, data: LoginResponse):
        self.use_physics = False
        if self.timer_task is None:
            self.last_frame_time = time_ms()
            self.timer_task = asyncio.create_task(self.timer())

    @EventDispatcher.subscribe(PositionResponse)
    async def _synchronize_player_position(self, data: PositionResponse):
        self.jump_ticks = 0
        self.use_physics = True
