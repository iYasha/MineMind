import asyncio

from minemind.protocols.v765.bot import Bot


async def main():
    await Bot().run_forever()


if __name__ == '__main__':
    asyncio.run(main())
