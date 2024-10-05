import asyncio
import time
import typing

from mc_protocol.client import Client
from mc_protocol.dispatcher import EventDispatcher
from mc_protocol.protocols.base import InteractionModule
from mc_protocol.protocols.v765.inbound.play import LoginResponse

if typing.TYPE_CHECKING:
    from mc_protocol.protocols.v765.bot import Bot


def time_ms() -> int:
    """
    Get current time in milliseconds
    """
    return time.perf_counter_ns() // 1_000_000


class Physics(InteractionModule):
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

    def __del__(self):
        if self.timer_task is not None:
            self.timer_task.cancel()

    async def on_tick(self, now: int):
        pass
        # print('tick', now)

    async def timer(self):
        while True:
            now = time_ms()
            delta_seconds = (now - self.last_frame_time) / 1000
            self.last_frame_time = now
            self.time_accumulator += delta_seconds
            self.catchup_ticks = 0
            while self.time_accumulator >= self.PHYSICS_TIME_STEP:
                await self.on_tick(now)
                self.time_accumulator -= self.PHYSICS_TIME_STEP
                self.catchup_ticks += 1
                if self.catchup_ticks >= self.max_catchup_ticks:
                    break
            await asyncio.sleep(self.PHYSICS_INTERVAL_MS / 1000)

    @EventDispatcher.subscribe(LoginResponse)
    async def _start_playing(self, data: LoginResponse):
        self.use_physics = False
        if self.timer_task is None:
            self.last_frame_time = time_ms()
            self.timer_task = asyncio.create_task(self.timer())
