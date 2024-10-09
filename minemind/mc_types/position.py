from minemind.mc_types.base import MCType, SocketReader


class Position(MCType):
    # Might have bugs, because it returns Position(60, 16767550193740, 4093640184) for the death position

    def __init__(self, x: int, y: int, z: int):
        self.x = x
        self.y = y
        self.z = z

    @classmethod
    async def from_stream(cls, reader: SocketReader, **kwargs) -> 'Position':
        bytes_struct = await reader.read(8)
        val = int.from_bytes(bytes_struct, 'big', signed=True)
        x = (val >> 38) & 0x3FFFFFF  # Mask 26 bits for x
        y = val & 0xFFF  # Mask 12 bits for y
        z = (val >> 12) & 0x3FFFFFF  # Mask 26 bits for z

        # Apply sign correction if needed
        if x >= 1 << 25:
            x -= 1 << 26
        if y >= 1 << 11:
            y -= 1 << 12
        if z >= 1 << 25:
            z -= 1 << 26

        return Position(x, y, z)

    def __repr__(self):
        return f'Position({self.x}, {self.y}, {self.z})'

    def __bytes__(self):
        return self.bytes

    @property
    def bytes(self) -> bytes:
        return (((self.x & 0x3FFFFFF) << 38) | ((self.z & 0x3FFFFFF) << 12) | (self.y & 0xFFF)).to_bytes(8, 'big')
