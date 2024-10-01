import asyncio
import zlib
from asyncio import StreamReader

from mc_protocol.mc_types import VarInt
from mc_protocol.states.enums import ConnectionState
from mc_protocol.states.events import OutboundEvent
from mc_protocol.utils import AsyncBytesIO


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

    async def send_packet(self, event: OutboundEvent) -> None:
        # https://wiki.vg/Protocol#Packet_format
        buffer = bytes(VarInt(event.packet_id)) + event.payload
        buffer_len = len(buffer)
        if self.threshold is None:
            packet = VarInt(buffer_len).bytes + buffer
        elif buffer_len >= self.threshold:
            data_length = VarInt(buffer_len).bytes
            compressed_data = zlib.compress(buffer)
            packet = data_length + compressed_data
            packet = VarInt(len(packet)).bytes + packet
        elif buffer_len < self.threshold:
            data_length = VarInt(0).bytes
            buffer = data_length + buffer
            packet = VarInt(len(buffer)).bytes + buffer
        else:
            raise ValueError('Invalid packet length')

        self.writer.write(packet)
        await self.writer.drain()

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
                compressed_data += await reader.read(
                    packet_length - len(compressed_data)
                    )  # so we try to read what is missing
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
