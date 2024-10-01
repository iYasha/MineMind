from asyncio import StreamReader

from mc_protocol.mc_types.varint import VarInt
from mc_protocol.mc_types.string import String
from mc_protocol.mc_types.uuid import UUID
from mc_protocol.mc_types.int import Int, UInt, Byte, UByte, Short, UShort, Long, ULong
from mc_protocol.mc_types.float import Float, Double
from mc_protocol.mc_types.boolean import Boolean
from mc_protocol.utils import AsyncBytesIO

SocketReader = StreamReader | AsyncBytesIO

__all__ = ('VarInt', 'String', 'UUID', 'Int', 'UInt', 'Byte', 'UByte', 'Short', 'UShort', 'Long', 'ULong', 'Boolean',
           'SocketReader', 'Float', 'Double')
