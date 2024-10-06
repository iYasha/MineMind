import abc
import io
import math
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


class Vector3:

    def __init__(self, x: float, y: float, z: float):
        # TODO: Probably better to use a Decimal or just Vector3 class
        self.x = x
        self.y = y
        self.z = z

    def translate(self, dx: float, dy: float, dz: float):
        self.x += dx
        self.y += dy
        self.z += dz

    def scale(self, scalar: int) -> 'Vector3':
        self.x *= scalar
        self.y *= scalar
        self.z *= scalar
        return self

    def __repr__(self):
        return f'<Vector3 {self.x=} {self.y=} {self.z=}>'

    def offset(self, dx: float | int, dy: float | int, dz: float | int, inplace: bool = False) -> 'Vector3':
        if inplace:
            self.x += dx
            self.y += dy
            self.z += dz
            return self
        return Vector3(self.x + dx, self.y + dy, self.z + dz)

    def floored(self, inplace: bool = False) -> 'Vector3':
        if inplace:
            self.x = math.floor(self.x)
            self.y = math.floor(self.y)
            self.z = math.floor(self.z)
            return self
        return Vector3(math.floor(self.x), math.floor(self.y), math.floor(self.z))
