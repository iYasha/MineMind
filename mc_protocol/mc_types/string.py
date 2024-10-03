from typing import Type

from mc_protocol.mc_types.base import MCType, SocketReader
from mc_protocol.mc_types.int import Int
from mc_protocol.mc_types.varint import VarInt


class String(MCType):
    def __init__(self, value: str | bytes):
        """
        Bytes should be in format len(encoded_string) + encoded_string
        """
        self.str_value = None
        self.bytes_value = None
        if isinstance(value, str):
            self.str_value = value
        elif isinstance(value, bytes):
            self.bytes_value = value
        else:
            raise TypeError('Value must be a str or bytes object')

    @classmethod
    async def from_stream(cls, reader: SocketReader, len_type: Type[VarInt] | Type[Int] = VarInt, **kwargs) -> 'String':
        length = await len_type.from_stream(reader)
        return cls((await reader.read(length.int)).decode('utf-8'))

    def __str__(self):
        if self.str_value is None:
            length, offset = VarInt._read_varint(self.bytes_value)
            self.str_value = self.bytes_value[offset : length + offset].decode('utf-8')
        return self.str_value

    def __bytes__(self):
        if self.bytes_value is None:
            encoded_str = self.str_value.encode('utf-8')
            self.bytes_value = VarInt(len(encoded_str)).bytes + encoded_str
        return self.bytes_value

    def __repr__(self):
        return f'String("{self.str}")'

    @property
    def str(self) -> str:
        return str(self)

    @property
    def bytes(self) -> bytes:
        return bytes(self)


class Identifier(String):
    pass
