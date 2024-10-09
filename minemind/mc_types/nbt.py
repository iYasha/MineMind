"""
Named Binary Tag (NBT) data types.

TODO: Make these types more usable by implementing dunder methods.
"""

from struct import Struct
from typing import TypeVar

from minemind import mc_types
from minemind.mc_types.base import MCType, SocketReader

TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12


T = TypeVar('T')


class Tag:
    mc_type: type[MCType]

    def __init__(self, name: mc_types.String | None = None, value: T | dict | list | MCType | bytes | None = None):
        self.name = name
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.name!r}, {self.value!r})'

    @classmethod
    async def get_name(cls, reader: SocketReader):
        return await mc_types.String.from_stream(reader, len_type=mc_types.UShort)

    @classmethod
    async def from_stream(cls, reader: SocketReader, has_name: bool = True):
        return cls(
            name=await cls.get_name(reader) if has_name else None,
            value=await cls.mc_type.from_stream(reader),
        )


class Byte(Tag):
    mc_type: type[MCType] = mc_types.Byte


class Short(Tag):
    mc_type: type[MCType] = mc_types.Short


class Int(Tag):
    mc_type: type[MCType] = mc_types.Int


class Long(Tag):
    mc_type: type[MCType] = mc_types.Long


class Float(Tag):
    mc_type: type[MCType] = mc_types.Float


class Double(Tag):
    mc_type: type[MCType] = mc_types.Double


class String(Tag):
    mc_type: type[MCType] = mc_types.String

    @classmethod
    async def from_stream(cls, reader: SocketReader, has_name: bool = True):
        name = await cls.get_name(reader) if has_name else None
        value = await cls.mc_type.from_stream(reader, len_type=mc_types.UShort)
        return cls(name=name, value=value)


class ByteArray(Tag):
    @classmethod
    async def from_stream(cls, reader: SocketReader, has_name: bool = True):
        name = await cls.get_name(reader) if has_name else None
        length = await mc_types.Int.from_stream(reader)
        return cls(
            name=name,
            value=await reader.read(length.int),
        )


class IntArray(Tag):
    @classmethod
    async def from_stream(cls, reader: SocketReader, has_name: bool = True):
        name = await cls.get_name(reader) if has_name else None
        length = await mc_types.Int.from_stream(reader)
        fmt = Struct(">" + str(length.int) + "i")
        return cls(
            name=name,
            value=list(fmt.unpack(await reader.read(fmt.size))),
        )


class LongArray(Tag):
    @classmethod
    async def from_stream(cls, reader: SocketReader, has_name: bool = True):
        name = await cls.get_name(reader) if has_name else None
        length = await mc_types.Int.from_stream(reader)
        fmt = Struct(">" + str(length.int) + "q")
        return cls(
            name=name,
            value=list(fmt.unpack(await reader.read(fmt.size))),
        )


class List(Tag):
    def __init__(self, name: mc_types.String | None = None, value: list | None = None, tag_type_id: int | None = None):
        super().__init__(name, value)
        self.tag_type_id = tag_type_id

    @classmethod
    async def from_stream(cls, reader: SocketReader, has_name: bool = True):
        name = await cls.get_name(reader) if has_name else None
        tag_type_id = await mc_types.Byte.from_stream(reader)
        length = await mc_types.Int.from_stream(reader)
        tags = []
        tag_type = TAG_REGISTRY.get(tag_type_id.int)
        if tag_type is None:
            raise ValueError('Unknown tag byte:', tag_type_id.int)
        for _ in range(length.int):
            tags.append(await tag_type.from_stream(reader, has_name=False))
        return cls(
            name=name,
            value=tags,
            tag_type_id=tag_type_id.int,
        )


class Compound(Tag):
    @classmethod
    async def from_stream(cls, reader: SocketReader, has_name: bool = True):
        tags = {}
        name = await cls.get_name(reader) if has_name else None
        while True:
            tag_byte = await mc_types.Byte.from_stream(reader)
            if tag_byte.int == TAG_END:
                break

            tag_type = TAG_REGISTRY.get(tag_byte.int)
            if tag_type is None:
                raise ValueError('Unknown tag byte:', tag_byte.int)

            tag = await tag_type.from_stream(reader)
            tags[tag.name] = tag

        return cls(
            name=name,
            value=tags,
        )


class NBT:
    """
    The difference between AnonymousNBT and NBT is that AnonymousNBT doesn't have a name.
    """

    @classmethod
    async def from_stream(cls, reader: SocketReader, is_anonymous: bool = False) -> T | None:
        first_tag_id = await mc_types.Byte.from_stream(reader)
        if first_tag_id.int == TAG_COMPOUND:
            return await Compound.from_stream(reader, has_name=not is_anonymous)
        tag_type = TAG_REGISTRY.get(first_tag_id.int)
        if tag_type is None:
            return None
        return await tag_type.from_stream(reader, not is_anonymous)


TAG_REGISTRY = {
    TAG_END: None,
    TAG_BYTE: Byte,
    TAG_SHORT: Short,
    TAG_INT: Int,
    TAG_LONG: Long,
    TAG_FLOAT: Float,
    TAG_DOUBLE: Double,
    TAG_BYTE_ARRAY: ByteArray,
    TAG_STRING: String,
    TAG_LIST: List,
    TAG_COMPOUND: Compound,
    TAG_INT_ARRAY: IntArray,
    TAG_LONG_ARRAY: LongArray,
}
