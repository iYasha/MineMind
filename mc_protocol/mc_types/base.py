import abc
from asyncio import StreamReader

import io


class AsyncBytesIO(io.BytesIO):

    async def read(self, *args, **kwargs) -> bytes:
        return super().read(*args, **kwargs)


SocketReader = StreamReader | AsyncBytesIO


class MCType(abc.ABC):

    @classmethod
    @abc.abstractmethod
    async def from_stream(cls, reader: SocketReader, **kwargs) -> 'MCType':
        raise NotImplementedError
