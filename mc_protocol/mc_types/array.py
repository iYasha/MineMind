from typing import TypeVar

from mc_protocol.mc_types.base import SocketReader, MCType

T = TypeVar('T')


class Array(list[T], MCType):

    @classmethod
    async def from_stream(cls, reader: SocketReader, length: int, mc_type: T) -> 'Array':
        instance = cls()
        for _ in range(length):
            instance.append(await mc_type.from_stream(reader))
        return instance


