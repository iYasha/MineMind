from asyncio import StreamReader


class Boolean:

    def __init__(self, value: bool | bytes):
        self.bool_value = None
        self.bytes_value = None

        if isinstance(value, bool):
            self.bool_value = value
        elif isinstance(value, bytes):
            self.bytes_value = value
        else:
            raise TypeError('Value must be a bool or bytes object')

    def __bool__(self):
        if self.bool_value is None:
            self.bool_value = bool(self.bytes_value)
        return self.bool_value

    def __bytes__(self):
        if self.bytes_value is None:
            self.bytes_value = bytes([self.bool_value])
        return self.bytes_value

    def __repr__(self):
        return f'Boolean({self.bool_value})'

    @property
    def bool(self) -> bool:
        return bool(self)

    @property
    def bytes(self) -> bytes:
        return bytes(self)

    @classmethod
    async def from_stream(cls, reader: StreamReader) -> 'Boolean':
        return cls(bool(await reader.read(1)))

