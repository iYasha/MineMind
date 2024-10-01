import asyncio

from mc_protocol.client import Client
from mc_protocol.event_loop import EventLoop
from mc_protocol.states.enums import HandshakingNextState


async def main():
    async with Client('localhost') as client:
        event_loop = EventLoop(client)
        loop = asyncio.create_task(event_loop.run_forever())
        print(await client.login(HandshakingNextState.STATUS))
        await loop


if __name__ == '__main__':
    asyncio.run(main())

