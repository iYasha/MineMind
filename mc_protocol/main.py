import asyncio

from mc_protocol.client import Client
from mc_protocol.dispatcher import EventDispatcher
from mc_protocol.protocols.v765.inbound.status import ServerInfoResponse
from mc_protocol.protocols.v765.player import Player


@EventDispatcher.subscribe(ServerInfoResponse)
async def server_status(data: ServerInfoResponse):
    print(data)


async def main():
    async with Client('localhost', protocol_version=765) as client:
        dispatcher = EventDispatcher(client)
        dispatcher_task = asyncio.create_task(dispatcher.run_forever())

        # server = Server(client)
        # print(await server.get_info())

        player = Player(client)
        await player.login('Notch')

        async with player.spawned():
            await player.chat_message('Hello, world!')

        await dispatcher_task


if __name__ == '__main__':
    asyncio.run(main())
