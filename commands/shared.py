from __future__ import annotations

_Client = None
_Session = None


async def GetClient():
    global _Client
    if _Client is None:
        from fishr import AsyncClient

        _Client = AsyncClient()
    return _Client


async def GetSession():
    global _Session
    if _Session is None:
        import aiohttp

        _Session = aiohttp.ClientSession()
    return _Session
