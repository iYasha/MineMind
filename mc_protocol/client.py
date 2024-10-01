import asyncio
import io
import json
import uuid
import zlib
from asyncio import StreamReader
from collections import Counter
from typing import NamedTuple

from mc_protocol.constants import ENTITIES
from mc_protocol.enums import State, ConnectionState
from mc_protocol.mc_types import VarInt, String, UUID, UShort, Boolean, Long, Short, Int
from mc_protocol.mc_types.float import Double, Float
from mc_protocol.schemas import StatusResponse
from mc_protocol.utils import AsyncBytesIO


class OfflinePlayerNamespace:
    bytes = b'OfflinePlayer:'


class Client:
    def __init__(self, host: str = '127.0.0.1', port: int = 25565, protocol_version: int = 767):
        self.host = host
        self.port = port
        self.protocol_version = protocol_version
        self.reader = None
        self.writer = None
        self.threshold = None
        self.state = ConnectionState.HANDSHAKING

        self.player_uuid: UUID | None = None
        self.player_entity_id: VarInt | None = None

    async def __aenter__(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.writer.close()
        await self.writer.wait_closed()

    def pack_packet(self, packet_id: int, data: bytes = b'') -> bytes:
        # https://wiki.vg/Protocol#Packet_format
        buffer = bytes(VarInt(packet_id)) + data
        buffer_len = len(buffer)
        if self.threshold is None:
            return VarInt(buffer_len).bytes + buffer
        elif buffer_len >= self.threshold:
            data_length = VarInt(buffer_len).bytes
            compressed_data = zlib.compress(buffer)
            packet = data_length + compressed_data
            return VarInt(len(packet)).bytes + packet
        elif buffer_len < self.threshold:
            data_length = VarInt(0).bytes
            buffer = data_length + buffer
            return VarInt(len(buffer)).bytes + buffer

    async def unpack_packet(self, reader: StreamReader) -> tuple[VarInt, AsyncBytesIO]:
        packet_length = await VarInt.from_stream(reader)
        if self.threshold is None:
            packet_id = await VarInt.from_stream(reader)
            data_length = packet_length.int - len(packet_id.bytes)
            data = await reader.read(data_length)
            return packet_id, AsyncBytesIO(data)
        data_length = await VarInt.from_stream(reader)
        if data_length.int != 0 and data_length.int >= self.threshold:
            packet_length = packet_length.int - len(data_length.bytes)

            compressed_data = await reader.read(packet_length)
            print(f'COMPRESSED DATA: {packet_length}')
            while len(compressed_data) < packet_length:  # sometimes the rest of the data hasn't been transmited yet
                print(f'READ ADDITIONAL PACKAGES: {packet_length - len(compressed_data)}')
                compressed_data += await reader.read(packet_length - len(compressed_data))  # so we try to read what is missing
            decompressed_data = zlib.decompress(compressed_data)  # TODO: Possible issues with compressed response
            if data_length.int != len(decompressed_data):
                raise zlib.error('Incorrect uncompressed data length')
            buffer = AsyncBytesIO(decompressed_data)
            packet_id = await VarInt.from_stream(buffer)
            return packet_id, buffer
        else:
            packet_id = await VarInt.from_stream(reader)
            data_length = packet_length.int - len(packet_id.bytes) - len(data_length.bytes)
            data = await reader.read(data_length)
            return packet_id, AsyncBytesIO(data)

    async def handshake(self, next_state: State):
        payload = (
            VarInt(self.protocol_version).bytes +
            String(self.host).bytes +
            UShort(self.port).bytes +  # Big-endian unsigned short
            next_state.value
        )

        self.writer.write(self.pack_packet(0x00, payload))
        await self.writer.drain()

        if next_state == State.LOGIN:
            self.state = ConnectionState.LOGIN
        elif next_state == State.STATUS:
            self.state = ConnectionState.STATUS
        else:
            raise ValueError(f'Invalid next state: {next_state}')

    async def server_status(self) -> StatusResponse:
        await self.handshake(State.STATUS)
        self.writer.write(self.pack_packet(0x00))
        await self.writer.drain()

        packet_id, data = await self.unpack_packet(self.reader)
        json_len = (await VarInt.from_stream(data)).int
        response_data = await data.read(json_len)
        json_data = json.loads(response_data.decode('utf-8'))
        return StatusResponse.model_validate(json_data)

    async def login_successful(self):
        packet_id, data = await self.unpack_packet(self.reader)
        self.player_uuid = await UUID.from_stream(data)

        username = await String.from_stream(data)

        properties_count = (await VarInt.from_stream(data)).int

        if properties_count != 0:
            # https://wiki.vg/Protocol#Login_Success
            raise NotImplementedError('Properties are not supported yet')

        is_strict_error_handling = await Boolean.from_stream(data)

        print(f'{packet_id=} {self.player_uuid=} {username=} {properties_count=} {is_strict_error_handling=}')

    async def login_start(self, user_name: str):
        user_uuid = UUID(uuid.uuid3(OfflinePlayerNamespace, user_name))

        payload = (
            String(user_name).bytes +
            user_uuid.bytes
        )
        self.writer.write(self.pack_packet(0x00, payload))
        await self.writer.drain()

        packet_id, data = await self.unpack_packet(self.reader)
        print(f'{packet_id=}')

        if packet_id.int == 1:
            server_id_length = (await VarInt.from_stream(data)).int
            server_id = await data.read(server_id_length)

            print(f'{server_id_length=} {server_id=}')

            public_key_length = (await VarInt.from_stream(data)).int
            public_key_bytes = await data.read(public_key_length)

            print(f'{public_key_length=} {public_key_bytes=}')

            verify_token_length = (await VarInt.from_stream(data)).int
            verify_token = await data.read(verify_token_length)

            print(f'{verify_token_length=} {verify_token=}')

            should_authenticate = bool(await data.read(1))
            print(f'{should_authenticate=}')
            raise NotImplementedError('Authentication is not supported yet')
        elif packet_id.int == 3:
            self.threshold = (await VarInt.from_stream(data)).int
            print(f'{self.threshold=}')
            await self.login_successful()
            await self.login_acknowledge()
        elif packet_id.int == 2:
            raise NotImplementedError('Encryption is not supported yet')

    async def login_acknowledge(self):
        self.writer.write(self.pack_packet(0x03))
        await self.writer.drain()
        self.state = ConnectionState.CONFIGURATION

        # 0x01 - Clientbound Plugin Message (configuration)
        packet_id, data = await self.unpack_packet(self.reader)
        print(f'FIRST UNPACKED {packet_id} {data.readlines()}')

        # 0x0C - Feature Flags
        packet_id, data = await self.unpack_packet(self.reader)
        print(f'FIRST UNPACKED {packet_id} {data.readlines()}')

        # 0x0E - Select Known Pack
        # or
        # 0x09 - Add Resource Pack (configuration)
        packet_id, data = await self.unpack_packet(self.reader)
        print(f'FIRST UNPACKED {packet_id}')
        if packet_id.int == 0xE:
            await self.select_known_packs(await data.read())
        else:
            print('ADD RESOURCE PACK', await data.read())

        print('-=' * 50)

        # if packet_id.int == 0x4 and self.state == ConnectionState.CONFIGURATION:
        #     keep_alive_id = await data.read(8)
        #     try:
        #         int.from_bytes(keep_alive_id, 'big', signed=True)  # long type
        #     except Exception as e:
        #         print('not alive')
        #     print('-=' * 50)
        #     print('KEEP ALIVE')
        #     await self.keep_alive(0x04, keep_alive_id)
        #     print('-=' * 50)

        await self.finish_configuration()

        await self.play()

    async def keep_alive(self, packet_id: int, keep_alive_id: bytes):
        self.writer.write(self.pack_packet(packet_id, keep_alive_id))
        await self.writer.drain()

    async def finish_configuration(self):
        self.writer.write(self.pack_packet(0x03))
        await self.writer.drain()
        self.state = ConnectionState.PLAY

    async def respawn(self):
        self.writer.write(self.pack_packet(0x09, VarInt(0).bytes))
        await self.writer.drain()
        print('RESPAWNED')

    async def select_known_packs(self, payload: bytes):
        print('SELECTED KNOWN PACKS', payload)
        self.writer.write(self.pack_packet(0x07, payload))
        await self.writer.drain()

    async def confirm_teleportation(self, teleport_id: VarInt) -> None:
        # play state
        self.writer.write(self.pack_packet(0x00, teleport_id.bytes))

    async def play(self):
        respawned = False
        most_sent_packets = Counter()
        Position = NamedTuple('Position', [
            ('x', Double), ('y', Double), ('z', Double),
            ('yaw', Float), ('pitch', Float),
        ])
        player_position: Position = None
        try:
            while True:
                packet_id, data = await self.unpack_packet(self.reader)
                most_sent_packets[packet_id.int] += 1

                if packet_id.int == 0x40:
                    print(f'Synchronize Player Position requested')
                    x, y, z = await Double.from_stream(data), await Double.from_stream(data), await Double.from_stream(
                        data
                    )
                    yaw, pitch = await Float.from_stream(data), await Float.from_stream(data)
                    flags = await data.read(1)
                    teleport_id = await VarInt.from_stream(data)
                    await self.confirm_teleportation(teleport_id)
                    player_position = Position(x=x, y=y, z=z, yaw=yaw, pitch=pitch)
                    print(f'Teleportation confirmed. Position: {x=} {y=} {z=} {yaw=} {pitch=} {flags=} {teleport_id=}')
                elif packet_id.int == 0x26:
                    keep_alive_id = await Long.from_stream(data)
                    await self.keep_alive(0x18, keep_alive_id.bytes)
                    print(f'KEEP ALIVE {keep_alive_id=}')
                elif packet_id.int == 0x48:
                    pass  # Set Head Rotation
                elif packet_id.int == 0x06:
                    pass  # block_destruction
                elif packet_id.int == 0x03:
                    pass  # animate
                elif packet_id.int == 0x2f:
                    pass  # Update Entity Position and Rotation
                elif packet_id.int == 0x30:
                    pass  # Update Entity Rotation
                elif packet_id.int == 0x64:
                    pass  # Update Time
                elif packet_id.int == 0x09:
                    pass  # Block Update
                elif packet_id.int == 0x5a:
                    pass  # Set Entity Velocity
                elif packet_id.int == 0x58:
                    pass  # Set Entity Metadata
                elif packet_id.int == 0x70:
                    pass  # Teleport Entity
                elif packet_id.int == 0x5B:
                    pass  # Set Equipment
                elif packet_id.int == 0x68:
                    pass  # Sound Effect
                elif packet_id.int == 0x49:
                    pass  # Update Section Blocks
                elif packet_id.int == 0x75:
                    pass  # Update Attributes
                elif packet_id.int == 0x00:
                    pass  # bundle_delimiter
                elif packet_id.int == 0x5d:
                    pass  # Set Health
                elif packet_id.int == 0x42:
                    pass  # Remove Entities
                elif packet_id.int == 0x07:
                    pass  # block_entity_data
                elif packet_id.int == 0x27:
                    pass  # Chunk Data and Update Light
                elif packet_id.int == 0x28:
                    pass  # World Event
                elif packet_id.int == 0x6f:
                    pass  # Pickup Item
                elif packet_id.int == 0x1a:
                    pass  # Damage Event
                elif packet_id.int == 0x24:
                    pass  # Hurt Animation
                elif packet_id.int == 0x29:
                    pass  # Particle
                elif packet_id.int == 0x2B:
                    self.player_entity_id = await Int.from_stream(data)
                    is_hardcore = await Boolean.from_stream(data)
                    dimension_count = await VarInt.from_stream(data)
                    print(f'PLAYER ENTITY ID {self.player_entity_id=}')

                elif packet_id.int == 0x2E:
                    # Update Entity Position
                    entity_id = await VarInt.from_stream(data)
                    delta_x = await Short.from_stream(data)
                    delta_y = await Short.from_stream(data)
                    delta_z = await Short.from_stream(data)
                    on_ground = await Boolean.from_stream(data)
                    # print(f'UPDATE ENTITY POSITION {entity_id=} {delta_x=} {delta_y=} {delta_z=} {on_ground=}')
                elif packet_id.int == 0x3C:
                    # Combat Death
                    player_id = await VarInt.from_stream(data)
                    text = await data.read()
                    if player_id.int == self.player_entity_id.int:
                        print(f'PLAYER DEATH {player_id=} {text=}')
                        await self.respawn()
                    else:
                        print(f'COMBAT DEATH {player_id=} {text=}')
                elif packet_id.int == 0x01:
                    # Spawn Entity
                    entity_id = await VarInt.from_stream(data)
                    entity_uuid = await UUID.from_stream(data)
                    entity_type = await VarInt.from_stream(data)
                    entity_type = ENTITIES.get(entity_type.int, {'id': 'unknown'})['id']
                    print(f'Entity spawned {entity_type=} {entity_id=} {entity_uuid=} {self.player_entity_id} {self.player_uuid}')
                else:
                    read_count = len(await data.read())
                    print(f'[New Packet ID: {packet_id.hex}] Received. Len: {read_count}')

                if not respawned:
                    respawned = True
                    await self.respawn()
        except BaseException as e:
            print(most_sent_packets)
            raise e

    async def login(self):
        await self.handshake(State.LOGIN)
        await self.login_start('Notch')
