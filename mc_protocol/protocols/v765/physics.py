from mc_protocol.client import Client
from mc_protocol.protocols.base import InteractionModule


class Physics(InteractionModule):

    def __int__(self, client: Client):
        self.client = client
