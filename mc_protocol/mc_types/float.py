import struct
from asyncio import StreamReader
from decimal import Decimal

from mc_protocol.mc_types.base import AsyncBytesIO


class Float:

    def __init__(self, value: int | float | bytes):
        self.float_value = None
        self.bytes_value = None

        if isinstance(value, float):
            self.float_value = value
        elif isinstance(value, int):
            self.float_value = float(value)
        elif isinstance(value, bytes):
            self.bytes_value = value
        else:
            raise TypeError('Value must be an int, float or bytes object')

    def __float__(self):
        if self.float_value is None:
            self.float_value = struct.unpack('>f', self.bytes_value)[0]
        return self.float_value

    def __bytes__(self):
        if self.bytes_value is None:
            self.bytes_value = struct.pack('>f', self.float_value)
        return self.bytes_value

    def __repr__(self):
        return f'Float({float(self)})'

    @classmethod
    async def from_stream(cls, reader: StreamReader | AsyncBytesIO) -> 'Float':
        return cls(await reader.read(4))

    @property
    def float(self) -> float:
        return float(self)

    @property
    def bytes(self) -> bytes:
        return bytes(self)


class Double:

    def __init__(self, value: Decimal | float | bytes):
        self.float_value = None
        self.bytes_value = None

        if isinstance(value, float):
            self.float_value = value
        elif isinstance(value, Decimal):
            self.float_value = float(value)
        elif isinstance(value, bytes):
            self.bytes_value = value
        else:
            raise TypeError('Value must be an float or bytes object')

    def __float__(self):
        if self.float_value is None:
            self.float_value = struct.unpack('>d', self.bytes_value)[0]
        return self.float_value

    def __bytes__(self):
        if self.bytes_value is None:
            self.bytes_value = struct.pack('>d', self.float_value)
        return self.bytes_value

    def __repr__(self):
        return f'Double({float(self)})'

    @classmethod
    async def from_stream(cls, reader: StreamReader | AsyncBytesIO) -> 'Double':
        return cls(await reader.read(8))

    @property
    def float(self) -> float:
        return float(self)

    @property
    def bytes(self) -> bytes:
        return bytes(self)

    @property
    def decimal(self) -> Decimal:
        return Decimal(self.float)
