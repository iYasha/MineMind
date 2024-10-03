import abc
import io
from asyncio import StreamReader


class AsyncBytesIO(io.BytesIO):
    async def read(self, *args, **kwargs) -> bytes:  # type: ignore[override]
        return super().read(*args, **kwargs)


SocketReader = StreamReader | AsyncBytesIO


class MCType(abc.ABC):
    @classmethod
    @abc.abstractmethod
    async def from_stream(cls, reader: SocketReader, **kwargs):
        raise NotImplementedError
