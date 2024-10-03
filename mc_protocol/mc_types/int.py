from mc_protocol.mc_types.base import MCType, SocketReader


class Int(MCType):
    size = 4  # size of the number type in bytes
    signed = True

    def __init__(self, value: int | bytes):
        self.int_value = None
        self.bytes_value = None

        if isinstance(value, int):
            self.int_value = value
        elif isinstance(value, bytes):
            self.bytes_value = value
        else:
            raise TypeError('Value must be an int or bytes object')

    def __int__(self):
        if self.int_value is None:
            self.int_value = int.from_bytes(self.bytes_value[: self.size], 'big', signed=self.signed)
        return self.int_value

    def __bytes__(self):
        if self.bytes_value is None:
            self.bytes_value = self.int_value.to_bytes(self.size, 'big', signed=self.signed)
        return self.bytes_value

    def __repr__(self):
        return f'Int({int(self)})'

    @classmethod
    async def from_stream(cls, reader: SocketReader, **kwargs):
        return cls(await reader.read(cls.size))

    @property
    def int(self) -> int:
        return int(self)

    @property
    def bytes(self) -> bytes:
        return bytes(self)


class UInt(Int):
    signed = False


class Byte(Int):
    size = 1


class UByte(Byte):
    signed = False


class Short(Int):
    size = 2


class UShort(Short):
    signed = False


class Long(Int):
    size = 8


class ULong(Long):
    signed = False
