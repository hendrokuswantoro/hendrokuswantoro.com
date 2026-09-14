"""The two ports of the map must not drift apart.

The static site and the Next.js port each carry their own copy of the style.
Nobody notices a difference between them until someone opens the port a year
from now and finds a map that lost half its layers. These tests hold the two
copies to the same shape, and they hold the token out of the repository.
"""

from __future__ import annotations

import re

from konftes import AKAR

PETA = (AKAR / "assets" / "js" / "peta.js").read_text(encoding="utf-8")
PORT = (AKAR / "next" / "components" / "WorkMap.tsx").read_text(encoding="utf-8")


def lapisan(sumber: str, awal: str, akhir: str) -> list[str]:
    i = sumber.index(awal)
    j = sumber.index(akhir, i)
    return re.findall(r'id: "([a-z0-9-]+)"', sumber[i:j])


STATIS = lapisan(PETA, "      layers: [", "\n      ]\n    };\n  }")
NEXTJS = lapisan(PORT, "    layers: [", "  } as StyleSpecification;")


def test_jumlah_lapisan_masuk_akal():
    assert len(STATIS) >= 30, f"the style lost layers, now {len(STATIS)}"


def test_urutan_lapisan_sama():
    """Order is not cosmetic. MapLibre places symbols from the top of the
    stack downwards, so a reordering silently changes which labels win."""
    assert STATIS == NEXTJS, (
        "the two ports disagree.\n"
        f"  only static: {[x for x in STATIS if x not in NEXTJS]}\n"
        f"  only next  : {[x for x in NEXTJS if x not in STATIS]}"
    )


def test_lapisan_nama_benar_benar_ada():
    """LAYER_NAMA drives the language switch. An id listed there that does
    not exist in the style means one layer stops switching language, and
    nothing raises."""
    blok = re.search(r"var LAYER_NAMA = \[(.*?)\];", PETA, re.S)
    assert blok, "LAYER_NAMA is gone"
    for id_ in re.findall(r'"([a-z0-9-]+)"', blok.group(1)):
        assert id_ in STATIS, f"LAYER_NAMA names {id_}, which the style does not draw"


def test_setiap_lapisan_nama_ikut_saklar_bahasa():
    """The other direction: a label layer missing from LAYER_NAMA keeps its
    first language forever."""
    blok = re.search(r"var LAYER_NAMA = \[(.*?)\];", PETA, re.S)
    terdaftar = set(re.findall(r'"([a-z0-9-]+)"', blok.group(1)))
    for id_ in STATIS:
        if id_.startswith("nama-"):
            assert id_ in terdaftar, f"{id_} draws names but never switches language"


def test_provinsi_lengkap():
    """Thirty eight, the number of provinces Indonesia has. Mapbox carries no
    state labels here, so the site carries them itself."""
    for sumber, label in ((PETA, "peta.js"), (PORT, "WorkMap.tsx")):
        blok = re.search(r"PROVINSI_ID = \{(.*?)\n  \};", sumber, re.S) or re.search(
            r"PROVINSI_ID = \{(.*?)\n\};", sumber, re.S
        )
        assert blok, f"{label}: PROVINSI_ID is gone"
        baris = re.findall(r'\["([^"]+)", "([^"]+)", (-?\d+\.?\d*), (-?\d+\.?\d*)\]', blok.group(1))
        assert len(baris) == 38, f"{label}: {len(baris)} provinces, expected 38"
        for indo, inggris, bujur, lintang in baris:
            assert 94 <= float(bujur) <= 142, f"{label}: {indo} sits outside Indonesia"
            assert -12 <= float(lintang) <= 7, f"{label}: {indo} sits outside Indonesia"


def test_nama_provinsi_sama_di_kedua_port():
    def daftar(sumber: str) -> list[str]:
        blok = re.search(r"PROVINSI_ID = \{(.*?)\n\s*\};", sumber, re.S)
        return re.findall(r'\["([^"]+)", "[^"]+", -?\d', blok.group(1))

    assert daftar(PETA) == daftar(PORT), "the province lists differ between ports"


def test_token_tidak_pernah_ikut():
    """Token Mapbox publik tetap kredensial, dan repositori tidak boleh
    membawanya. konfigurasi.js ditulis saat build dan ada di .gitignore.

    `.env` dikecualikan, dan pengecualian itu ada sebabnya yang mahal. Aturan
    lama melarang tokennya ada di sana juga, jadi satu satunya salinan di
    mesin pengembangan hidup di konfigurasi.js, berkas yang ditimpa tiap kali
    `tools/bangun_situs.sh` dijalankan. Tokennya hilang begitu saja, dan yang
    memberitahu bukan pesan galat melainkan empat uji peta yang gagal dengan
    alasan yang menuduh kodenya. Lihat docs/pemecahan-masalah.md.

    `.env` justru tempat yang benar: ia ada di .gitignore, seluruh alat di
    repositori ini membacanya, dan tidak ada satu pun jalan ia ikut git.
    Yang dijaga uji ini adalah berkas yang BISA ikut git.
    """
    abaikan = {"dist", "node_modules", ".git", ".next", "out"}
    for berkas in AKAR.rglob("*"):
        if not berkas.is_file() or abaikan & set(berkas.parts):
            continue
        if berkas.name in {"konfigurasi.js", ".env"}:
            continue
        if berkas.suffix in {".zip", ".png", ".webp", ".svg", ".ico"}:
            continue
        try:
            isi = berkas.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        assert not re.search(r"\bpk\.eyJ[A-Za-z0-9]", isi), f"{berkas} carries a Mapbox token"


def test_konfigurasi_diabaikan_git():
    abaikan = (AKAR / ".gitignore").read_text(encoding="utf-8")
    assert "assets/js/konfigurasi.js" in abaikan


def test_maplibre_terkunci():
    """MapLibre adalah satu satunya kode pihak ketiga yang sampai ke
    pengunjung. Versinya dikunci di satu berkas supaya berkas pustaka, angka
    yang dicatat, dan yang diminta port Next.js tidak bisa berpisah jalan.

    Sejak 6.x pustakanya terbit sebagai ES module dan terpecah empat berkas.
    Keempatnya wajib ada: tanpa maplibre-gl-worker.mjs peta memuat gayanya
    lalu diam selamanya, tanpa galat apa pun.
    """
    dasar = AKAR / "assets" / "vendor" / "maplibre"
    versi = (dasar / "VERSI").read_text(encoding="utf-8").strip()
    # Berkasnya duduk di dalam folder bernama versinya, bukan di samping
    # VERSI. Alasannya di tools/versi_aset.py: maplibre-gl.mjs mengimpor
    # maplibre-gl-shared.mjs secara relatif, jadi query pada modul induk
    # tidak menurun ke anaknya, dan anak yang basi sama merusaknya.
    rumah = dasar / versi

    for nama in ("maplibre-gl.mjs", "maplibre-gl-shared.mjs",
                 "maplibre-gl-worker.mjs", "maplibre-gl.css"):
        assert (rumah / nama).exists(), f"{nama} hilang dari assets/vendor/maplibre"

    kepala = (rumah / "maplibre-gl.mjs").read_text(encoding="utf-8", errors="ignore")[:600]
    assert f"/v{versi}/" in kepala, f"berkas pustaka bukan versi {versi}"

    assert not (rumah / "maplibre-gl.js").exists() and not (dasar / "maplibre-gl.js").exists(), (
        "bundel UMD lama masih ada, dan versinya membawa GHSA-jrc7-96c5-q579"
    )

    paket = (AKAR / "next" / "package.json").read_text(encoding="utf-8")
    mayor = versi.split(".")[0]
    assert f'"maplibre-gl": "^{mayor}.' in paket, (
        f"port Next.js meminta mayor yang berbeda dari {versi} yang dibawa"
    )


def test_versi_maplibre_sudah_di_atas_ghsa():
    """GHSA-jrc7-96c5-q579 baru diperbaiki di 6.4.1. Turun di bawahnya berarti
    membawa kembali celah sanitizer yang sudah ditutup."""
    versi = (AKAR / "assets" / "vendor" / "maplibre" / "VERSI").read_text(
        encoding="utf-8").strip()
    angka = tuple(int(x) for x in versi.split("."))
    assert angka >= (6, 4, 1), f"MapLibre {versi} masih terdampak GHSA-jrc7-96c5-q579"


def test_worker_boleh_dari_origin_sendiri():
    """MapLibre 6 memuat workernya sebagai modul dari origin ini lewat
    import.meta.url. Dengan worker-src blob: saja, peta memuat gayanya lalu
    diam tanpa satu pun permintaan ubin dan tanpa galat."""
    headers = (AKAR / "_headers").read_text(encoding="utf-8")
    csp = [b for b in headers.splitlines() if "Content-Security-Policy:" in b][0]
    worker = [b for b in csp.split(";") if "worker-src" in b][0]
    assert "'self'" in worker, "worker-src menolak origin sendiri, peta akan diam"


def test_csp_menahan_muatan_sanitizer():
    """The CSP is what stops GHSA-jrc7-96c5-q579 from executing: an inline
    event handler needs 'unsafe-inline' in script-src, and there is none.
    Adding it would quietly turn an unexploitable advisory into a live one."""
    headers = (AKAR / "_headers").read_text(encoding="utf-8")
    csp = [b for b in headers.splitlines() if "Content-Security-Policy:" in b][0]
    naskah = [b for b in csp.split(";") if "script-src" in b][0]
    assert "unsafe-inline" not in naskah, (
        "script-src accepted unsafe-inline, which un-mitigates the MapLibre "
        "sanitizer bypass. See docs/keamanan.md."
    )


# ------------------------------------------------- peta dan kartu bertaut ---

# Sampai hari ini tautannya satu arah. Popup penanda membawa pembaca ke
# kartunya, tetapi dari kartu tidak ada jalan kembali ke peta, dan satu
# tampilan peta tidak bisa dibagikan sama sekali. Uji di bawah menjaga
# keduanya tetap terpasang.

HALAMAN = (AKAR / "project.html").read_text(encoding="utf-8")

KARYA = re.findall(r'\{ id: "([a-z0-9-]+)", kind: "', PETA)


def test_karya_terbaca_dari_peta():
    assert len(KARYA) == 7, f"terbaca {len(KARYA)} karya di peta.js, bukan 7"


def test_tiap_kartu_punya_jalan_kembali_ke_peta():
    ditaut = re.findall(r'data-peta-buka="([a-z0-9-]+)"', HALAMAN)
    assert sorted(ditaut) == sorted(KARYA), (
        "kartu dan penanda tidak lagi sepadan.\n"
        f"  hanya di kartu   : {sorted(set(ditaut) - set(KARYA))}\n"
        f"  hanya di peta.js : {sorted(set(KARYA) - set(ditaut))}"
    )


def test_tautan_ke_peta_ikut_berganti_bahasa():
    for baris in re.findall(r"<a[^>]*data-peta-buka=[^>]*>", HALAMAN):
        assert "data-ind=" in baris, f"tautan ini tidak punya bahasa Indonesianya: {baris}"


def test_tautan_ke_peta_juga_alamat_yang_bisa_disalin():
    """href-nya bukan "#". Yang ditekan pembaca dan yang tersalin dari bilah
    alamat harus alamat yang sama, kalau tidak tautannya tidak bisa dibagikan."""
    for slug in KARYA:
        pola = r'<a[^>]*href="#peta-%s"[^>]*data-peta-buka="%s"' % (slug, slug)
        assert re.search(pola, HALAMAN), f"{slug}: href dan data-peta-buka tidak sepadan"


def test_peta_membaca_alamat_yang_dibagikan():
    assert 'var AWALAN_HASH = "#peta-";' in PETA, "awalan alamatnya hilang"
    assert "function idDariHash()" in PETA
    assert 'addEventListener("hashchange"' in PETA, (
        "tanpa hashchange, tautan di kartu hanya mengubah alamat dan petanya diam"
    )
    assert "replaceState" in PETA, (
        "alamatnya tidak pernah ditulis balik, jadi tampilan peta tidak bisa disalin"
    )


def test_terbang_menuliskan_alamatnya():
    """flyToWork dipakai penanda maupun Jelajah. Kalau ia berhenti menulis
    alamat, yang tersalin dari bilah alamat bukan lagi yang sedang dilihat."""
    blok = re.search(r"function flyToWork\(entry, openPopup\) \{(.*?)\n    \}", PETA, re.S)
    assert blok, "flyToWork hilang"
    assert "tulisHash(entry.item.id)" in blok.group(1)


def test_saringan_legenda_diumumkan():
    """Angka di legenda berubah di layar tanpa bunyi. Tanpa wilayah aria-live
    ini, pembaca layar yang menyaring menurut jenis tidak mendengar apa apa."""
    assert 'kabar.setAttribute("aria-live", "polite")' in PETA
    assert "TEXT.filterOn" in PETA and "TEXT.filterOff" in PETA
    for kunci in ("filterOn", "filterOff", "focus"):
        assert re.search(r"\n    %s: \{ en: \"[^\"]+\", ind: \"[^\"]+\" \}" % kunci, PETA), (
            f"{kunci} tidak dwibahasa"
        )


def test_wilayah_kabar_di_luar_panel_yang_bisa_dilipat():
    """.peta__legenda.is-collapsed menyembunyikan .peta__grup dengan
    display:none, dan aria-live di dalam elemen tersembunyi tidak pernah
    dibacakan. Karena itu wilayah kabar duduk di dalam bagian petanya."""
    gaya = (AKAR / "assets" / "css" / "style.css").read_text(encoding="utf-8")
    assert ".peta__legenda.is-collapsed .peta__grup { display: none; }" in gaya
    assert "section.insertBefore(kabar" in PETA, (
        "wilayah kabar tidak lagi disisipkan ke bagian petanya"
    )


def test_kedua_port_sama_sama_membaca_alamat():
    """Port Next punya salinan petanya sendiri. Fitur yang hanya dipasang di
    satu port adalah cara paling sunyi kedua salinan ini berpisah."""
    for nama, sumber in (("peta.js", PETA), ("WorkMap.tsx", PORT)):
        assert '"#peta-"' in sumber, f"{nama}: awalan alamatnya hilang"
        assert "idDariHash" in sumber, f"{nama}: tidak membaca alamat"
        assert "replaceState" in sumber, f"{nama}: tidak menulis alamat"
        assert '"hashchange"' in sumber, f"{nama}: tidak mendengar pergantian alamat"
        assert 'aria-live", "polite"' in sumber or 'aria-live="polite"' in sumber, (
            f"{nama}: wilayah kabar pembaca layar hilang"
        )
        assert "peta__kabar" in sumber, f"{nama}: wilayah kabar hilang"


def test_kedua_port_tidak_lagi_menggantung_pada_load():
    """"load" tidak datang kalau satu sumber ubinnya ditolak, dan petanya
    tetap tergambar. Menggantungkan penataan padanya berarti relief tidak
    terpasang dan legenda tinggal kosong, tanpa satu galat pun."""
    for nama, sumber in (("peta.js", PETA), ("WorkMap.tsx", PORT)):
        assert "sudahSiap" in sumber, f"{nama}: penjaga sekali jalan hilang"
        for peristiwa in ('"load"', '"styledata"', '"idle"'):
            assert peristiwa in sumber, f"{nama}: tidak lagi mendengar {peristiwa}"
        assert "setTimeout(siap, 4000)" in sumber, f"{nama}: jaring pengamannya hilang"


def test_server_uji_memakai_nama_domain_bukan_alamat_ip():
    """Mapbox menolak alamat IP di pembatasan URL token.

    Kalimatnya tersurat di console.mapbox.com: "IP addresses are not supported
    in URL restrictions. Use a domain name instead." Selama server uji
    menjawab di 127.0.0.1, asalnya tidak akan pernah bisa didaftarkan, dan
    empat uji peta akan dilewati selamanya di tiap mesin dan di CI.

    Uji ini yang menahan alamatnya tetap berupa nama.
    """
    konf = (AKAR / "tests" / "conftest.py").read_text(encoding="utf-8")
    inang = re.search(r'INANG_UJI = "([^"]+)"', konf)
    assert inang, "INANG_UJI hilang dari conftest"
    nama = inang.group(1)
    assert not re.fullmatch(r"[0-9.]+|\[?[0-9a-f:]+\]?", nama), (
        f"server uji menjawab di {nama}, dan Mapbox menolak alamat IP"
    )
    assert f'yield f"http://{{INANG_UJI}}:{{porta}}"' in konf, (
        "fixture situs tidak lagi memakai INANG_UJI"
    )


def test_server_uji_mengikat_kedua_tumpukan():
    """localhost menunjuk ke dua alamat, dan urutannya berbeda antara Windows
    dan Linux. Server yang cuma mengikat satu membuat tiap permintaan menunggu
    tenggang sambungan lebih dulu: terukur 2050 ms lawan 16 ms."""
    konf = (AKAR / "tests" / "conftest.py").read_text(encoding="utf-8")
    assert 'socket.AF_INET, "127.0.0.1"' in konf
    assert 'socket.AF_INET6, "::1"' in konf
