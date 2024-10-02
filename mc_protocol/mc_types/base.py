from asyncio import StreamReader

import io


class AsyncBytesIO(io.BytesIO):

    async def read(self, *args, **kwargs) -> bytes:
        return super().read(*args, **kwargs)


SocketReader = StreamReader | AsyncBytesIO

