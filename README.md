# MineMind

Low-level API for creating minecraft bots.


## Supported Versions

- 1.20.3

## Installation

```bash
pip install minemind
```

## Example

Say hello world to the server.
````python
import asyncio
from mc_protocol.protocols.v765.bot import Bot

async def main():
    async with Bot(username='Steve', host='localhost', port=25565) as bot:
        await bot.chat_message('Hello, world!')

if __name__ == '__main__':
    asyncio.run(main())
````

React to different events.
````python
import asyncio
from mc_protocol.dispatcher import EventDispatcher
from mc_protocol.protocols.v765.bot import Bot
from mc_protocol.protocols.v765.inbound.play import CollectResponse

@EventDispatcher.subscribe(CollectResponse)
async def pickup_item(data: CollectResponse):
    print(f'Bot picked up {data.pickup_item_count} items')

async def main():
    await Bot().run_forever()

if __name__ == '__main__':
    asyncio.run(main())
````

Get server information.
````python
import asyncio

from mc_protocol.client import Client
from mc_protocol.protocols.v765.server import Server

async def main():
    async with Client(host='localhost', port=25565) as client:
        server = Server(client)
        print(await server.get_info())

if __name__ == '__main__':
    asyncio.run(main())
````

## Documentation
TBD

### Testing
To test your bot, you can start simple local server using docker (it's using itzg/minecraft-server image):
```bash
docker-compose up
````

### Debugging
Library provides three levels of debugging:
- [DEBUG=3] DEBUG_GAME_EVENTS: Print game events, like player movement, chat messages, damage received, etc.
- [DEBUG=2] DEBUG_PROTOCOL: Print all protocol messages, like handshaking, received events, map loading, etc. + DEBUG_GAME_EVENTS
- [DEBUG=1] DEBUG_TRACE: Lower socket level debugging, like connection status, sent and received packets, etc. + DEBUG_PROTOCOL

You can set the debug level by setting the environment variable `DEBUG` to one of the values above, e.g. to set debug level to `DEBUG_PROTOCOL`:
```bash
DEBUG=2 python my_script.py
```

## Roadmap

- [x] Physics engine
- [ ] Bot movement
- [ ] Elytra flight
- [ ] Combat system
- [ ] Mining
- [ ] Inventory management
- [ ] Item interaction (e.g. bed, crafting table, etc.)
- [ ] Implement crafting
- [ ] Pathfinding
- [ ] Fishing
- [ ] Documentation
- [ ] Unit-tests
- [ ] Dynamic version support

## Useful links

- Minecraft protocol documentations: https://wiki.vg/Protocol_version_numbers 
- Minecraft data (e.g. entities, protocol schema, etc.): https://github.com/PrismarineJS/minecraft-data/

## Contributing
Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Contact
If you have any questions, feel free to contact me via email: [ivan@simantiev.com](mailto:ivan@simantiev.com)
