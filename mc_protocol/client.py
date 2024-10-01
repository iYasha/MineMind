import asyncio
import io
import json
import uuid
import zlib
from asyncio import StreamReader

from mc_protocol.enums import State, ConnectionState
from mc_protocol.mc_types import VarInt, String, UUID, UShort, Boolean
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
            uncompressed_data = zlib.decompress(compressed_data)
            buffer = AsyncBytesIO(uncompressed_data)
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
        packet_size = await VarInt.from_stream(self.reader)
        if packet_size.int >= self.threshold:
            # compressed
            pass
        else:
            # uncompressed
            data_size = await VarInt.from_stream(self.reader)  # 0 to indicate uncompressed
            pocket_id = await VarInt.from_stream(self.reader)
            uuid_player = await UUID.from_stream(self.reader)

            username = await String.from_stream(self.reader)

            properties_count = (await VarInt.from_stream(self.reader)).int

            if properties_count != 0:
                # https://wiki.vg/Protocol#Login_Success
                raise NotImplementedError('Properties are not supported yet')

            is_strict_error_handling = await Boolean.from_stream(self.reader)

            print(f'{data_size=} {pocket_id=} {uuid_player=} {username=} {properties_count=} {is_strict_error_handling=}')

    async def login_start(self, user_name: str):
        user_uuid = UUID(uuid.uuid3(OfflinePlayerNamespace, user_name))

        payload = (
            String(user_name).bytes +
            user_uuid.bytes
        )
        self.writer.write(self.pack_packet(0x00, payload))
        await self.writer.drain()

        total_length = await VarInt.from_stream(self.reader)
        packet_id = await VarInt.from_stream(self.reader)
        print(f'{total_length=}, {packet_id=}')

        if packet_id.int == 1:
            server_id_length = (await VarInt.from_stream(self.reader)).int
            server_id = await self.reader.read(server_id_length)

            print(f'{server_id_length=} {server_id=}')

            public_key_length = (await VarInt.from_stream(self.reader)).int
            public_key_bytes = await self.reader.read(public_key_length)

            print(f'{public_key_length=} {public_key_bytes=}')

            verify_token_length = (await VarInt.from_stream(self.reader)).int
            verify_token = await self.reader.read(verify_token_length)

            print(f'{verify_token_length=} {verify_token=}')

            should_authenticate = bool(await self.reader.read(1))
            print(f'{should_authenticate=}')
            raise NotImplementedError('Authentication is not supported yet')
        elif packet_id.int == 3:
            self.threshold = (await VarInt.from_stream(self.reader)).int
            print(f'{self.threshold=}')
            await self.login_successful()
            await self.login_acknowledge()
        elif packet_id.int == 2:
            raise NotImplementedError('Encryption is not supported yet')

    async def login_acknowledge(self):
        self.writer.write(self.pack_packet(0x03))
        await self.writer.drain()
        self.state = ConnectionState.CONFIGURATION

        print(f'{self.threshold=}')

        # 0x01 - Clientbound Plugin Message (configuration)
        package_len = (await VarInt.from_stream(self.reader)).int
        data_len = (await VarInt.from_stream(self.reader)).int
        packet_id = (await VarInt.from_stream(self.reader)).int
        print(f'{package_len=} {data_len=} {hex(packet_id)=}')
        print(await self.reader.read(package_len))

        # 0x0C - Feature Flags
        package_len = (await VarInt.from_stream(self.reader)).int
        data_len = (await VarInt.from_stream(self.reader)).int
        packet_id = (await VarInt.from_stream(self.reader)).int
        print(f'{package_len=} {data_len=} {hex(packet_id)=}')
        print(await self.reader.read(package_len))

        # 0x0E - Select Known Pack
        # or
        # 0x09 - Add Resource Pack (configuration)
        package_len = (await VarInt.from_stream(self.reader)).int
        data_len = (await VarInt.from_stream(self.reader)).int
        packet_id = (await VarInt.from_stream(self.reader)).int
        print(f'{package_len=} {data_len=} {hex(packet_id)=}')
        if packet_id == 0xE:
            data = await self.reader.read(package_len)
            await self.select_known_packs(data)
        else:
            print(await self.reader.read(package_len))

        print('-=' * 50)

        await self.finish_configuration()

        await self.play()

    async def keep_alive(self, keep_alive_id: bytes):
        self.writer.write(self.pack_packet(0x04, keep_alive_id))
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
        self.writer.write(self.pack_packet(0x07, payload))
        await self.writer.drain()
        print('SELECTED KNOWN PACKS')

    async def play(self):
        respawned = False
        while True:
            package_len = (await VarInt.from_stream(self.reader)).int
            data_len = (await VarInt.from_stream(self.reader)).int
            packet_id = (await VarInt.from_stream(self.reader)).int
            print('RECEIVED PACKAGE')
            print(f'{package_len=} {data_len=} {hex(packet_id)=}')
            if packet_id == 0x4:
                keep_alive_id = await self.reader.read(8)
                try:
                    int.from_bytes(keep_alive_id, 'big', signed=True)  # long type
                except Exception as e:
                    print('not alive')
                print('-=' * 50)
                print('KEEP ALIVE')
                await self.keep_alive(keep_alive_id)
                print('-=' * 50)
            else:
                read_count = len(await self.reader.read(package_len))
                print('READ', read_count)
                # if data_len - read_count > 0:
                #     print('EXTRA', read_count - data_len, 'BYTES', len(await self.reader.read(read_count - data_len)))

            if not respawned:
                respawned = True
                await self.respawn()




    async def login(self):
        await self.handshake(State.LOGIN)
        await self.login_start('Notch')
