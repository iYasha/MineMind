from mc_protocol.mc_types.base import SocketReader, MCType


class Position(MCType):
    # Might have bugs, because it returns Position(60, 16767550193740, 4093640184) for the death position

    def __init__(self, x: int, y: int, z: int):
        self.x = x
        self.y = y
        self.z = z

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> 'Position':
        bytes_struct = await reader.read(8)
        val = int.from_bytes(bytes_struct, 'big', signed=False)
        x = val >> 38
        y = (val << 52) >> 52
        z = (val << 26) >> 38
        return Position(x, y, z)

    def __repr__(self):
        return f'Position({self.x}, {self.y}, {self.z})'

    def __bytes__(self):
        return self.bytes

    @property
    def bytes(self) -> bytes:
        return (((self.x & 0x3FFFFFF) << 38) | ((self.z & 0x3FFFFFF) << 12) | (self.y & 0xFFF)).to_bytes(8, 'big')
