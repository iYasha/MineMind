from asyncio import StreamReader
from typing import Tuple

from mc_protocol.utils import AsyncBytesIO


class VarInt:

    def __init__(self, value: int | bytes) -> None:
        self.int_value = None
        self.bytes_value = None

        if isinstance(value, int):
            self.int_value = value
        elif isinstance(value, bytes):
            self.bytes_value = value
        else:
            raise TypeError('Value must be an int or bytes object')

    @classmethod
    async def from_stream(cls, reader: StreamReader | AsyncBytesIO) -> 'VarInt':
        num_read = 0
        result = 0
        while True:
            byte = await reader.read(1)
            if not byte:
                raise IOError("Connection closed unexpectedly")
            value = byte[0]
            result |= (value & 0x7F) << (7 * num_read)

            num_read += 1
            if num_read > 5:
                raise IOError("VarInt is too big")

            if (value & 0x80) == 0:
                break
        return cls(result)

    @classmethod
    def _read_varint(cls, data: bytes, offset: int = 0) -> Tuple[int, int]:
        """
        Reads a VarInt from the given data starting at the specified offset.

        :param data: The byte array to read the VarInt from.
        :param offset: The starting position in the byte array.
        :return: A tuple containing the VarInt and the number of bytes read.
        :raises IndexError: If there is not enough data to read a VarInt.
        """
        num_read = 0
        result = 0
        while True:
            if offset >= len(data):
                raise IndexError("Not enough data to read VarInt")
            byte = data[offset]
            result |= (byte & 0x7F) << (7 * num_read)  # Extract 7 bits and shift
            num_read += 1
            offset += 1
            if (byte & 0x80) == 0:  # MSB is 0, stop reading
                break
        return result, num_read  # Return the VarInt and number of bytes read

    @classmethod
    def _write_varint(cls, value: int) -> bytes:
        """
        Writes a VarInt to bytes.

        :param value: The integer value to encode as a VarInt.
        :return: A bytes object containing the VarInt representation.
        """
        result = bytearray()
        while True:
            temp = value & 0x7F  # Get the last 7 bits
            value >>= 7  # Right shift the value by 7 bits
            if value != 0:
                result.append(temp | 0x80)  # Set the MSB to indicate more bytes to follow
            else:
                result.append(temp)  # Last byte, no more bytes to follow
                break
        return bytes(result)

    def __int__(self):
        if self.int_value is None:
            self.int_value, _ = self._read_varint(self.bytes_value)
        return self.int_value

    def __bytes__(self):
        if self.bytes_value is None:
            self.bytes_value = self._write_varint(self.int_value)
        return self.bytes_value

    def __repr__(self):
        return f'VarInt({self.int})'

    @property
    def bytes(self) -> bytes:
        return bytes(self)

    @property
    def int(self) -> int:
        return int(self)

    @property
    def hex(self) -> int:
        return hex(int(self))


