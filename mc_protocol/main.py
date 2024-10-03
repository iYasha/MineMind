import asyncio

from mc_protocol.client import Client
from mc_protocol.event_loop import EventLoop
from mc_protocol.mc_types.base import SocketReader
from mc_protocol.protocols.v765.inbound.status import ServerInfoResponse
from mc_protocol.protocols.v765.player import Player


@EventLoop.subscribe(ServerInfoResponse)
async def server_status(data: SocketReader):
    instance = await ServerInfoResponse.from_stream(data)
    print(instance)


async def main():
    async with Client('localhost', protocol_version=765) as client:
        event_loop = EventLoop(client)
        loop = asyncio.create_task(event_loop.run_forever())

        # server = Server(client)
        # print(await server.get_info())

        player = Player(client)
        await player.login('Notch')

        async with player.spawned():
            await player.chat_message('Hello, world!')

        await loop


if __name__ == '__main__':
    asyncio.run(main())
