from typing import TypeVar

from mc_protocol.mc_types.base import MCType, SocketReader

T = TypeVar('T', bound=MCType)


class Array(list[T], MCType):
    @classmethod
    async def from_stream(cls, reader: SocketReader, length: int, mc_type: type[T], **kwargs) -> 'Array[T]':  # type: ignore[override]
        instance: Array[T] = cls()
        for _ in range(length):
            instance.append(await mc_type.from_stream(reader))
        return instance
