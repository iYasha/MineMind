import uuid
from asyncio import StreamReader


class UUID:

    def __init__(self, value: uuid.UUID | bytes) -> None:
        self.uuid_value = None
        self.bytes_value = None
        if isinstance(value, uuid.UUID):
            self.uuid_value = value
        elif isinstance(value, bytes):
            self.bytes_value = value
        else:
            raise TypeError('Value must be a uuid.UUID or bytes object')

    def __bytes__(self):
        if self.bytes_value is None:
            self.bytes_value = self.uuid_value.bytes
        return self.bytes_value

    @classmethod
    async def from_stream(cls, reader: StreamReader) -> 'UUID':
        return cls(uuid.UUID(bytes=await reader.read(16)))

    @property
    def uuid(self) -> uuid.UUID:
        if self.uuid_value is None:
            self.uuid_value = uuid.UUID(bytes=self.bytes_value)
        return self.uuid_value

    def __repr__(self):
        return f'UUID("{self.uuid_value}")'

    @property
    def bytes(self) -> bytes:
        return bytes(self)


