from __future__ import annotations

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

JALUR_PEKA = ("/api/v1/auth", "/api/v1/keamanan", "/api/v1/admin")


class TanpaSimpan:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope.get("path", "").startswith(JALUR_PEKA):
            await self.app(scope, receive, send)
            return

        async def kirim(pesan: Message) -> None:
            if pesan["type"] == "http.response.start":
                kepala = MutableHeaders(scope=pesan)
                kepala["Cache-Control"] = "no-store"
                kepala["Pragma"] = "no-cache"
            await send(pesan)

        await self.app(scope, receive, kirim)
