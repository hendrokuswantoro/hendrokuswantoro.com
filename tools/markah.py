"""Markdown ke HTML, hanya sebatas yang dipakai blog ini.

Kenapa bukan pustaka Markdown yang sudah ada: situs ini tidak punya satu pun
dependensi runtime, dan langkah build-nya berjalan di mesin Cloudflare yang
tidak dijamin punya pip. Menambah satu paket demi empat bentuk markup adalah
kompleksitas yang dilarang bab 15.1.

Kenapa tidak berbahaya: pengurai ini **menolak** apa pun yang tidak dikenalnya
dengan galat yang menyebut nomor barisnya. Pengurai setengah jadi yang diam
diam menghasilkan HTML salah jauh lebih berbahaya daripada pengurai kecil yang
berhenti dan mengadu.

Yang didukung:

    ## Judul bagian              -> <h2>
    Paragraf biasa               -> <p>
    > Kutipan                    -> <blockquote><p>
    - butir                      -> <ul><li>
    1. butir                     -> <ol><li>
    ![keterangan](/unggahan/x)   -> <figure><img>
    !video[keterangan](/ung/x)   -> <figure><video>
    **tebal**  *miring*          -> <strong> <em>
    `kode`                       -> <code>
    [teks](alamat)               -> <a href>

Yang ditolak dengan galat: heading selain ##, tabel, blok kode berpagar,
HTML mentah, dan tautan referensi.

Daftar, gambar, dan video ditambahkan 18 September 2026, bersama bilah
format di dashboard admin. Sampai hari itu ketiganya ditolak, dan itu
memang benar selama tidak ada satu pun cara mengunggah berkas: gambar yang
menunjuk ke mana saja adalah gambar yang menunjuk ke server orang lain.
Sekarang alamatnya dibatasi ke berkas yang memang diunggah ke sini, dan
pembatasan itu ditegakkan di sini, di pengurai, bukan di antarmukanya.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass


class MarkahSalah(ValueError):
    """Sintaks yang tidak didukung, disertai nomor baris."""


@dataclass(frozen=True)
class Blok:
    """Satu blok tingkat atas.

    `jenis` salah satu dari h2, p, quote, ul, ol, gambar, video.

    `teks` isi bloknya. Untuk gambar dan video ia keterangannya, dan boleh
    kosong. Untuk ul dan ol ia selalu kosong; butirnya di `butir`.

    `alamat` hanya terisi untuk gambar dan video. `butir` hanya terisi untuk
    ul dan ol. Keduanya sengaja bukan subkelas terpisah: yang membaca Blok
    ada tiga tempat, dan tiga tempat yang harus tahu tujuh kelas lebih mudah
    tertinggal daripada tiga tempat yang membaca satu kelas.
    """

    jenis: str
    teks: str
    baris: int
    alamat: str = ""
    butir: tuple[str, ...] = ()


DITOLAK = [
    (re.compile(r"^\s{0,3}#(?!#\s)"), "hanya '## ' yang didukung untuk judul"),
    (re.compile(r"^\s{0,3}#{3,}\s"), "hanya '## ' yang didukung untuk judul"),
    (re.compile(r"^\s{0,3}(```|~~~)"), "blok kode berpagar belum didukung"),
    (re.compile(r"^\s{0,3}\|"), "tabel belum didukung"),
    (re.compile(r"^\s{0,3}<"), "HTML mentah tidak diterima"),
]

GAMBAR = re.compile(r"^!\[(?P<teks>[^\]]*)\]\((?P<alamat>[^)\s]+)\)$")
VIDEO = re.compile(r"^!video\[(?P<teks>[^\]]*)\]\((?P<alamat>[^)\s]+)\)$")
BUTIR_UL = re.compile(r"^\s{0,3}[-*+]\s+(?P<teks>.+)$")
BUTIR_OL = re.compile(r"^\s{0,3}\d{1,3}\.\s+(?P<teks>.+)$")

# Berkas yang boleh disebut gambar dan video, dan dari mana saja.
#
# Hanya berkas yang memang diunggah ke situs ini. Gambar dari server orang
# lain terdengar praktis dan tidak: tiap pembaca yang membuka tulisannya
# mengirimkan alamat IP-nya ke server itu tanpa pernah memintanya, gambarnya
# hilang pada hari pemiliknya merapikan berkasnya, dan Content-Security-Policy
# situs ini memang sudah menolaknya, jadi yang terbit adalah kotak kosong.
# Ditolak di sini berarti penulisnya tahu sebelum menekan Simpan.
AWALAN_MEDIA = ("/unggahan/", "/assets/img/")
AKHIRAN_GAMBAR = (".webp", ".avif", ".png", ".jpg", ".jpeg", ".gif")
AKHIRAN_VIDEO = (".mp4", ".webm")

# Ukuran gambar dititipkan di nama berkasnya, misalnya
# "9f3c1a7b2d4e5f60-1600x900.webp".
#
# Kenapa di nama berkas dan bukan di markahnya: yang menuliskannya mesin
# pengunggah, bukan orang, jadi ia tidak pernah salah ketik dan tidak pernah
# lupa. Kenapa tidak dibaca dari berkasnya saat membangun: pembangkit situs
# statis dan validator API berjalan di dua mesin yang berbeda, dan yang satu
# tidak punya berkasnya.
#
# Tanpa ukuran, peramban baru tahu tinggi gambarnya sesudah mengunduhnya, dan
# tulisan di bawahnya melompat. Itu bukan soal rapi: pembaca yang sedang
# membaca kalimat kehilangan tempatnya.
UKURAN = re.compile(r"-(\d{1,5})x(\d{1,5})\.[a-z0-9]+$")

SEBARIS = re.compile(
    r"(?P<kode>`[^`]+`)"
    r"|(?P<tautan>\[[^\]]+\]\([^)\s]+\))"
    r"|(?P<tebal>\*\*[^*]+\*\*)"
    r"|(?P<miring>\*[^*]+\*)"
)


def periksa_media(alamat: str, jenis: str) -> None:
    """Menolak alamat gambar dan video yang tidak berasal dari situs ini."""
    if not alamat.startswith(AWALAN_MEDIA):
        raise MarkahSalah(
            f"alamat {jenis} harus berkas yang diunggah ke situs ini, "
            f"yaitu diawali {' atau '.join(AWALAN_MEDIA)}. "
            f"Yang ditulis: {alamat[:60]!r}"
        )
    if ".." in alamat:
        raise MarkahSalah(f"alamat {jenis} tidak boleh memuat '..': {alamat[:60]!r}")

    boleh = AKHIRAN_GAMBAR if jenis == "gambar" else AKHIRAN_VIDEO
    if not alamat.lower().endswith(boleh):
        raise MarkahSalah(
            f"berkas {jenis} harus berakhiran {', '.join(boleh)}. "
            f"Yang ditulis: {alamat[:60]!r}"
        )


def ukuran(alamat: str) -> tuple[int, int] | None:
    """Lebar dan tinggi yang dititipkan di nama berkasnya, kalau ada."""
    cocok = UKURAN.search(alamat)
    if cocok is None:
        return None
    return int(cocok.group(1)), int(cocok.group(2))


def blok(sumber: str) -> list[Blok]:
    """Memecah Markdown jadi blok tingkat atas, atau melempar MarkahSalah."""
    hasil: list[Blok] = []
    kumpul: list[str] = []
    butir: list[str] = []
    mulai = 0
    jenis = "p"

    def tutup() -> None:
        nonlocal kumpul, butir, jenis, mulai
        if butir:
            hasil.append(Blok(jenis, "", mulai, butir=tuple(butir)))
        elif kumpul:
            hasil.append(Blok(jenis, " ".join(kumpul).strip(), mulai))
        kumpul = []
        butir = []
        jenis = "p"

    for nomor, baris in enumerate(sumber.splitlines(), 1):
        isi = baris.rstrip()

        if not isi.strip():
            tutup()
            continue

        if isi.lstrip().startswith("## "):
            tutup()
            hasil.append(Blok("h2", isi.lstrip()[3:].strip(), nomor))
            continue

        # Gambar dan video berdiri sendiri satu baris penuh.
        #
        # Yang diperiksa lebih dulu bentuknya, dan yang bentuknya hampir benar
        # ditolak dengan galat, bukan dibiarkan turun jadi paragraf. Sebuah
        # "![peta](/unggahan/a b.webp)" yang lolos jadi paragraf akan terbit
        # sebagai tanda seru dan kurung siku di tengah tulisan, dan penulisnya
        # baru tahu sesudah membaca halaman yang sudah terbit.
        telanjang = isi.lstrip()
        if telanjang.startswith("!"):
            for pola, ini in ((VIDEO, "video"), (GAMBAR, "gambar")):
                cocok = pola.match(telanjang)
                if cocok is None:
                    continue
                tutup()
                alamat = cocok.group("alamat")
                try:
                    periksa_media(alamat, ini)
                except MarkahSalah as galat:
                    raise MarkahSalah(f"baris {nomor}: {galat}") from galat
                hasil.append(
                    Blok(ini, cocok.group("teks").strip(), nomor, alamat=alamat)
                )
                break
            else:
                raise MarkahSalah(
                    f"baris {nomor}: bentuk gambar atau video tidak dikenali. "
                    "Yang benar: ![keterangan](/unggahan/berkas.webp) "
                    "atau !video[keterangan](/unggahan/berkas.mp4)\n"
                    f"  {isi[:70]}"
                )
            continue

        if telanjang.startswith(">"):
            if jenis != "quote":
                tutup()
                jenis, mulai = "quote", nomor
            kumpul.append(telanjang[1:].strip())
            continue

        # Daftar. Satu baris satu butir; butir yang dilanjutkan ke baris
        # berikutnya belum didukung, dan tidak didukung diam diam: baris
        # lanjutan tanpa tanda butir menutup daftarnya dan mulai jadi
        # paragraf, persis seperti yang terlihat di layar.
        for pola, ini in ((BUTIR_UL, "ul"), (BUTIR_OL, "ol")):
            cocok = pola.match(isi)
            if cocok is None:
                continue
            if jenis != ini:
                tutup()
                jenis, mulai = ini, nomor
            butir.append(cocok.group("teks").strip())
            break
        else:
            for pola, alasan in DITOLAK:
                if pola.match(isi):
                    raise MarkahSalah(f"baris {nomor}: {alasan}\n  {isi[:70]}")

            if butir:
                tutup()
            if not kumpul:
                mulai = nomor
            kumpul.append(isi.strip())

    tutup()
    # Tautan diperiksa di sini, bukan hanya saat HTML-nya dibangkitkan.
    #
    # Bedanya penting. Yang memanggil blok() adalah dua pihak: pembangkit
    # situs statis, dan validator skema yang menjaga jalur tulis API. Kalau
    # pemeriksaannya hanya ada di sebaris(), tulisan bertautan javascript:
    # akan diterima API dengan tenang, tersimpan di basis data, dan baru
    # meledak berhari hari kemudian saat situsnya dibangun ulang, jauh dari
    # orang yang menulisnya dan dari sebabnya.
    for b in hasil:
        for potong in (b.teks, *b.butir):
            try:
                sebaris(potong)
            except MarkahSalah as galat:
                raise MarkahSalah(f"baris {b.baris}: {galat}") from galat

    return hasil


# Skema yang boleh muncul di dalam href.
#
# Escape saja tidak cukup, dan itu ditemukan lewat penyisiran, bukan lewat
# membaca kode. `[klik](javascript:alert(1))` lolos sempurna: alamatnya
# di-escape dengan benar, lalu dipasang apa adanya ke dalam href, dan
# hasilnya tautan yang menjalankan JavaScript begitu diklik. Sama untuk
# `data:text/html`, yang membuka halaman karangan penulisnya di atas asal
# situs ini.
#
# Penulisnya memang hanya pemilik situs, dan itu justru alasan kenapa ini
# diperbaiki, bukan alasan membiarkannya: "hanya admin yang bisa" adalah
# anggapan yang gugur pada hari ada penulis kedua atau ada akun yang diambil
# orang.
SKEMA_BOLEH = ("https:", "http:", "mailto:")


def periksa_alamat(alamat: str) -> None:
    """Menolak, bukan membersihkan diam diam.

    Alamat yang dibersihkan tanpa sepengetahuan penulisnya akan terbit jadi
    tautan yang menuju tempat lain daripada yang dimaksudnya, dan itu lebih
    membingungkan daripada pesan galat.
    """
    bersih = alamat.strip()

    # Relatif: jangkar, akar, atau tetangga. Tidak punya skema sama sekali.
    if bersih.startswith(("#", "/", "./", "../")):
        return

    kecil = bersih.lower()
    if kecil.startswith(SKEMA_BOLEH):
        return

    # Tanpa titik dua berarti relatif juga, misalnya "tentang.html".
    if ":" not in kecil.split("/")[0]:
        return

    raise MarkahSalah(
        f"skema tautan tidak diizinkan: {bersih[:40]!r}. "
        f"Yang boleh: {', '.join(SKEMA_BOLEH)}, atau alamat relatif."
    )


def sebaris(teks: str) -> str:
    """Markup sebaris jadi HTML. Selain itu di-escape."""
    keluar: list[str] = []
    posisi = 0

    for cocok in SEBARIS.finditer(teks):
        keluar.append(html.escape(teks[posisi:cocok.start()], quote=False))
        potong = cocok.group(0)

        if cocok.lastgroup == "kode":
            keluar.append("<code>" + html.escape(potong[1:-1], quote=False) + "</code>")
        elif cocok.lastgroup == "tautan":
            label, _, alamat = potong[1:-1].partition("](")
            periksa_alamat(alamat)
            keluar.append(
                '<a href="%s">%s</a>'
                % (html.escape(alamat, quote=True), html.escape(label, quote=False))
            )
        elif cocok.lastgroup == "tebal":
            keluar.append("<strong>" + html.escape(potong[2:-2], quote=False) + "</strong>")
        else:
            keluar.append("<em>" + html.escape(potong[1:-1], quote=False) + "</em>")

        posisi = cocok.end()

    keluar.append(html.escape(teks[posisi:], quote=False))
    return "".join(keluar)


def polos(teks: str) -> str:
    """Teks tanpa markup, aman untuk atribut biasa. Tanda kutipnya di-escape."""
    bersih = SEBARIS.sub(_telanjangi, teks)
    return html.escape(bersih, quote=True)


def untuk_ind(teks: str) -> str:
    """Teks tanpa markup untuk atribut data-ind, di-escape DUA kali.

    Satu kali tidak cukup, dan itu ditemukan audit 26 September 2026.
    Peramban membuka satu lapis escape saat atribut dibaca, lalu
    assets/js/app.js memasang nilainya lewat innerHTML. Dengan satu lapis,
    `&lt;a href=...&gt;` di atribut kembali jadi tag sungguhan di halaman
    berbahasa Indonesia. Dengan dua lapis, yang sampai ke innerHTML masih
    `&lt;`, dan yang tergambar tanda kurang dari, bukan tag.

    Untuk data-ind-alt dan atribut lain yang dipasang lewat setAttribute,
    pakai polos(): di sana tidak ada innerHTML yang membuka lapis kedua.
    """
    return html.escape(polos(teks), quote=True)


def _telanjangi(cocok: re.Match[str]) -> str:
    potong = cocok.group(0)
    if cocok.lastgroup == "kode":
        return potong[1:-1]
    if cocok.lastgroup == "tautan":
        return potong[1:-1].partition("](")[0]
    if cocok.lastgroup == "tebal":
        return potong[2:-2]
    return potong[1:-1]
