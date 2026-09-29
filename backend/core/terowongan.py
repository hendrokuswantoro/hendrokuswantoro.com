from __future__ import annotations

import asyncio
import functools
import ipaddress

import jwt
from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from backend.core.konfigurasi import pengaturan

PENANDA_CLOUDFLARE = ("cf-ray", "cf-connecting-ip", "cf-access-jwt-assertion")
AWALAN_BOLEH = ("/admin/", "/_next/", "/api/", "/unggahan/")

IZIN = (
    "accelerometer=(), autoplay=(), browsing-topics=(), camera=(), display-capture=(), "
    "encrypted-media=(), fullscreen=(self), geolocation=(), gyroscope=(), hid=(), "
    "interest-cohort=(), magnetometer=(), microphone=(), midi=(), payment=(), "
    "screen-wake-lock=(), serial=(), usb=(), xr-spatial-tracking=()"
)
IZIN_ADMIN = IZIN.replace("camera=()", "camera=(self)")

UMUM = {
    "X-Content-Type-Options": "nosniff",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "X-Permitted-Cross-Domain-Policies": "none",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
}

CSP_ADMIN_BAWAAN = (
    "default-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; "
    "img-src 'self' data: blob:; style-src 'self'; font-src 'self'; script-src 'self' blob:; "
    "worker-src 'self' blob:; child-src blob:; frame-src 'none'; connect-src 'self'; "
    "object-src 'none'; upgrade-insecure-requests"
)
CSP_NEXT = (
    "default-src 'none'; img-src 'self'; media-src 'self'; base-uri 'none'; "
    "form-action 'none'; frame-ancestors 'none'"
)
CSP_API = "default-src 'none'; frame-ancestors 'none'"


def kepala_untuk(jalur: str, csp_aplikasi: str = "") -> dict[str, str]:
    kepala = dict(UMUM)
    if jalur == "/admin" or jalur.startswith("/admin/"):
        kepala["Permissions-Policy"] = IZIN_ADMIN
        kepala["Cross-Origin-Embedder-Policy"] = "require-corp"
        kepala["X-Robots-Tag"] = "noindex, nofollow"
        kepala["Content-Security-Policy"] = csp_aplikasi or CSP_ADMIN_BAWAAN
    elif jalur.startswith("/_next/"):
        kepala["Permissions-Policy"] = IZIN
        kepala["X-Robots-Tag"] = "noindex, nofollow"
        kepala["Content-Security-Policy"] = CSP_NEXT
    else:
        kepala["Permissions-Policy"] = IZIN
        kepala["Content-Security-Policy"] = CSP_API
    return kepala


@functools.lru_cache
def _kunci(tim: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(
        f"https://{tim}.cloudflareaccess.com/cdn-cgi/access/certs", cache_keys=True, lifespan=3600
    )


def periksa_akses(token: str, tim: str, aud: str) -> bool:
    try:
        kunci = _kunci(tim).get_signing_key_from_jwt(token).key
        jwt.decode(
            token,
            kunci,
            algorithms=["RS256"],
            audience=aud,
            issuer=f"https://{tim}.cloudflareaccess.com",
            options={"require": ["exp", "iat", "aud", "iss"]},
        )
    except Exception:
        return False
    return True


def _loopback(alamat: str) -> bool:
    try:
        return ipaddress.ip_address(alamat).is_loopback
    except ValueError:
        return False


def _alamat_sah(alamat: str) -> bool:
    try:
        ipaddress.ip_address(alamat)
    except ValueError:
        return False
    return True


def _jalur_boleh(jalur: str) -> bool:
    return jalur == "/admin" or jalur.startswith(AWALAN_BOLEH)


class Terowongan:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        atur = pengaturan()
        masuk = Headers(scope=scope)
        inang = masuk.get("host", "").rsplit(":", 1)[0].lower()
        lewat = bool(atur.terowongan_host) and inang == atur.terowongan_host.lower()
        if not (lewat or any(nama in masuk for nama in PENANDA_CLOUDFLARE)):
            await self.app(scope, receive, send)
            return

        jalur = scope.get("path", "")

        async def tolak(kode: int, alasan: str) -> None:
            jawaban = JSONResponse({"detail": alasan}, status_code=kode, headers=kepala_untuk(jalur))
            await jawaban(scope, receive, send)

        if not (atur.terowongan_host and atur.access_tim and atur.access_aud):
            await tolak(503, "terowongan belum lengkap: isi TEROWONGAN_HOST, ACCESS_TIM, dan ACCESS_AUD")
            return

        token = masuk.get("cf-access-jwt-assertion", "")
        if not token or not await asyncio.to_thread(periksa_akses, token, atur.access_tim, atur.access_aud):
            await tolak(403, "permintaan ini tidak lewat Cloudflare Access")
            return

        if not _jalur_boleh(jalur):
            await tolak(404, "tidak ada")
            return

        klien = scope.get("client")
        asli = masuk.get("cf-connecting-ip", "")
        if klien and _loopback(klien[0]) and _alamat_sah(asli):
            scope = dict(scope, client=(asli, 0))

        async def kirim(pesan: Message) -> None:
            if pesan["type"] == "http.response.start":
                keluar = MutableHeaders(scope=pesan)
                csp_aplikasi = keluar.get("x-hk-csp", "")
                if "x-hk-csp" in keluar:
                    del keluar["x-hk-csp"]
                for nama, nilai in kepala_untuk(jalur, csp_aplikasi).items():
                    keluar[nama] = nilai
            await send(pesan)

        await self.app(scope, receive, kirim)
