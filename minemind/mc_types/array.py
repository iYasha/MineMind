from typing import Any, TypeVar

from minemind.mc_types.base import MCType, SocketReader
from minemind.mc_types.int import Long
from minemind.mc_types.varnum import VarInt

T = TypeVar('T', bound=MCType)


class Array(list[T], MCType):
    @classmethod
    async def from_stream(cls, reader: SocketReader, length: int | None, mc_type: type[T], **kwargs):  # type: ignore[override]
        type_params = kwargs.get('type_params', {})
        instance: Array[T] = cls()
        if length is None:
            length = (await VarInt.from_stream(reader)).int
        for _ in range(length):
            instance.append(await mc_type.from_stream(reader, **type_params))
        return instance

    def get(self, index: int, default: Any = None) -> T | None:
        try:
            return self[index]
        except IndexError:
            return default


class BitSet(Array[Long]):

    @classmethod
    async def from_stream(cls, reader: SocketReader, **kwargs) -> 'BitSet':  # type: ignore[override]
        length = await VarInt.from_stream(reader)
        return await super().from_stream(reader, length.int, Long, **kwargs)  # type: ignore[return-value]
