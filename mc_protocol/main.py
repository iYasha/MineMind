import asyncio

from mc_protocol.client import Client


async def main():
    async with Client('localhost') as client:
        print(await client.login())


if __name__ == '__main__':
    asyncio.run(main())

