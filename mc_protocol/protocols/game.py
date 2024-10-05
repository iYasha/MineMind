from mc_protocol.client import Client
from mc_protocol.dispatcher import EventDispatcher
from mc_protocol.protocols.base import InteractionModule
from mc_protocol.protocols.v765.constants import DIMENSIONS
from mc_protocol.protocols.v765.inbound.play import LoginResponse, RespawnResponse


class Game(InteractionModule):
    DIFFICULTIES = ['peaceful', 'easy', 'normal', 'hard']
    GAME_MODES = ['survival', 'creative', 'adventure', 'spectator']

    def __init__(self, client: Client):
        self.client = client
        self.game_mode = self.GAME_MODES[0]
        self.difficulty = self.DIFFICULTIES[0]
        self.is_flat = False
        self.is_hardcore = False
        self.dimension = 'overworld'
        self.min_y = 0
        self.height = 256

    def set_game_mode(self, game_mode: int):
        self.game_mode = self.GAME_MODES[game_mode & 0b11]

    @EventDispatcher.subscribe(LoginResponse)
    async def on_login(self, event: LoginResponse):
        self.set_game_mode(event.game_mode.int)
        self.is_hardcore = event.is_hardcore.bool
        self.dimension = event.dimension_type.str.split(':')[1]
        self.is_flat = event.is_flat.bool
        self.min_y = DIMENSIONS[self.dimension]['minY']  # type: ignore[assignment]
        self.height = DIMENSIONS[self.dimension]['height']  # type: ignore[assignment]

    @EventDispatcher.subscribe(RespawnResponse)
    async def on_respawn(self, event: RespawnResponse):
        self.set_game_mode(event.game_mode.int)
        self.dimension = event.dimension_type.str.split(':')[1]
        self.is_flat = event.is_flat.bool
        self.min_y = DIMENSIONS[self.dimension]['minY']  # type: ignore[assignment]
        self.height = DIMENSIONS[self.dimension]['height']  # type: ignore[assignment]
