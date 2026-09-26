from __future__ import annotations

import re

import pytest

from konftes import AKAR

ADMIN = AKAR / "next" / "components" / "admin"
BILAH = (ADMIN / "BilahFormat.tsx").read_text(encoding="utf-8")
PUSTAKA = (ADMIN / "PanelBerkas.tsx").read_text(encoding="utf-8")
PENYUNTING = (ADMIN / "PenyuntingTulisan.tsx").read_text(encoding="utf-8")
API = (AKAR / "next" / "lib" / "api.ts").read_text(encoding="utf-8")
LAYANAN = (AKAR / "backend" / "layanan" / "berkas.py").read_text(encoding="utf-8")


@pytest.mark.parametrize("judul", [
    "Tebal", "Miring", "Judul bagian", "Kutipan",
    "Daftar butir", "Daftar bernomor", "Kode", "Tautan",
])
def test_bilah_punya_tombol_yang_sama_dengan_pengolah_kata(judul):
    assert f'judul: "{judul}"' in BILAH, f"tombol {judul} hilang dari bilah format"


@pytest.mark.parametrize("markah,nama", [
    ("**", "tebal"),
    ("## ", "judul bagian"),
    ("> ", "kutipan"),
    ("- ", "daftar butir"),
    ("1. ", "daftar bernomor"),
])
def test_tanda_yang_ditulis_bilah_memang_yang_dikenal_pengurai(markah, nama):
    assert f'depan: "{markah}"' in BILAH, f"{nama} menulis tanda yang lain"


@pytest.mark.parametrize("huruf", ["b", "i", "k"])
def test_pintasan_papan_tik_yang_sudah_dihafal_orang(huruf):
    assert f"{huruf}: {{ depan:" in BILAH, f"Ctrl+{huruf.upper()} tidak terpasang"


def test_pintasan_dipasang_pada_kotaknya_bukan_pada_dokumen():
    assert "el.addEventListener" in BILAH
    assert "document.addEventListener" not in BILAH


def test_tumpukan_urung_peramban_tidak_dibuang():
    assert 'execCommand("insertText"' in BILAH
    assert "if (!berhasil)" in BILAH


def test_pratinjau_dibangun_server_bukan_pengurai_kedua_di_peramban():
    assert "pratinjauTulisan" in PENYUNTING
    assert "/api/v1/admin/pratinjau" in API


@pytest.mark.parametrize("tanda", ["**", "## ", "](", "blockquote"])
def test_tidak_ada_pengurai_markah_kedua_di_penyunting(tanda):
    hasil = re.findall(r"replace\(.*" + re.escape(tanda), PENYUNTING)
    assert hasil == [], f"ada yang mengurai {tanda!r} sendiri di penyunting"


def test_pratinjau_tidak_dibersihkan_lagi_di_peramban():
    assert "dangerouslySetInnerHTML" in PENYUNTING
    assert "DOMPurify" not in PENYUNTING and "sanitize" not in PENYUNTING


def test_media_disisipkan_ke_kedua_bahasa_sekaligus():
    assert "[kotakEn.current, kotakId.current]" in PENYUNTING


@pytest.mark.parametrize("bentuk", ['"!video[]("', '"![]("'])
def test_bentuk_sisipan_sama_dengan_yang_diterima_pengurai(bentuk):
    assert bentuk in PENYUNTING


def test_layar_unggah_menyebut_soal_lokasi_di_dalam_foto():
    assert "koordinat" in PUSTAKA
    assert "tidak dibuang" in PUSTAKA
    assert 'id="buang-metadata"' in PUSTAKA, "tidak ada kotak centangnya"
    assert "buangMetadata" in PUSTAKA


def test_kotak_buang_metadata_mati_secara_bawaan():
    assert "useState(false);" in PUSTAKA.split("buangMetadata")[1][:40], (
        "kotak buang metadata tidak mati secara bawaan"
    )


def test_layar_unggah_menyebut_jenis_yang_tidak_bisa_dibuang():
    assert "GIF dan AVIF" in PUSTAKA


def test_jenis_yang_ditawarkan_peramban_sama_dengan_yang_diterima_server():
    cocok = re.search(r'accept="([^"]+)"', PUSTAKA)
    assert cocok, "input berkas tanpa accept"
    ditawarkan = set(cocok.group(1).split(","))

    diterima = set(re.findall(r'"((?:image|video)/[a-z0-9.+-]+)":', LAYANAN))
    assert diterima, "daftar tipe di layanan tidak terbaca"
    assert ditawarkan == diterima, (
        f"hanya di peramban: {sorted(ditawarkan - diterima)}, "
        f"hanya di server: {sorted(diterima - ditawarkan)}"
    )


def test_unggahan_memakai_xhr_supaya_kemajuannya_terlihat():
    assert "XMLHttpRequest" in API
    assert "upload.onprogress" in API


def test_content_type_tidak_dipasang_tangan_untuk_multipart():
    potong = API[API.index("function sekaliUnggah"):API.index("export async function unggahBerkas")]
    assert "Content-Type" not in potong


def test_unggahan_diulang_sekali_kalau_tokennya_mati_di_tengah_jalan():
    potong = API[API.index("export async function unggahBerkas"):]
    assert "auth/refresh" in potong[:1500]


def test_port_next_mengenal_jenis_blok_yang_sama_dengan_pengurainya():
    posts = (AKAR / "next" / "content" / "posts.ts").read_text(encoding="utf-8")
    markah_py = (AKAR / "tools" / "markah.py").read_text(encoding="utf-8")

    di_next = set(re.findall(r'\{ kind: "([a-z0-9]+)"', posts))

    di_pengurai = set(re.findall(r'Blok\(\s*"([a-z0-9]+)"', markah_py))
    di_pengurai |= set(re.findall(r'\(\s*(?:BUTIR_UL|BUTIR_OL|VIDEO|GAMBAR),\s*"([a-z0-9]+)"\)', markah_py))
    di_pengurai |= set(re.findall(r'jenis(?:, mulai)? = "([a-z0-9]+)"', markah_py))

    assert di_next == di_pengurai, (
        f"hanya di port Next: {sorted(di_next - di_pengurai)}, "
        f"hanya di pengurai: {sorted(di_pengurai - di_next)}"
    )


@pytest.mark.parametrize("jenis", ["ul", "ol", "gambar", "video"])
def test_port_next_benar_benar_menggambar_jenis_barunya(jenis):
    tampilan = (AKAR / "next" / "components" / "PostView.tsx").read_text(encoding="utf-8")
    assert f'block.kind === "{jenis}"' in tampilan, f"{jenis} tidak digambar port Next"
