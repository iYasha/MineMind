import io


class AsyncBytesIO(io.BytesIO):

    async def read(self, *args, **kwargs) -> bytes:
        return super().read(*args, **kwargs)