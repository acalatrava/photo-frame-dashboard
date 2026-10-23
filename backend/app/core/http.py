import httpx


class TooLarge(Exception):
    pass


async def get_limited(client: httpx.AsyncClient, url: str, max_bytes: int) -> httpx.Response:
    """GET that refuses to read more than max_bytes, so a hostile or broken server cannot exhaust memory."""
    async with client.stream("GET", url) as r:
        declared = r.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > max_bytes:
            raise TooLarge(f"respuesta de más de {max_bytes // 1024} KB")
        body = bytearray()
        async for chunk in r.aiter_bytes():
            body.extend(chunk)
            if len(body) > max_bytes:
                raise TooLarge(f"respuesta de más de {max_bytes // 1024} KB")
        r._content = bytes(body)
        return r
