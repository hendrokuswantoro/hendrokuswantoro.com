"""Bilah format dan pustaka berkas di dashboard admin.

Yang dijaga di sini bukan tampilannya, melainkan empat keputusan yang mudah
sekali hilang saat berkasnya disunting lagi bulan depan:

1. Yang disimpan tetap teks markah, bukan HTML dari peramban.
2. Pratinjaunya dibangun server, oleh pengurai yang sama dengan yang dipakai
   Simpan. Pengurai kedua di peramban akan berpisah dari yang pertama, dan
   layar pratinjau yang berbohong lebih buruk daripada tidak ada pratinjau.
3. Gambar dan video disisipkan ke KEDUA bahasa sekaligus, sebab dua bahasa
   wajib sebangun blok demi blok.
4. Layar unggahnya mengatakan metadata foto tidak dibuang. Peringatan adalah
   bagian yang paling mudah hilang saat sebuah teks dipendekkan, sebab ia
   bagian yang paling tidak menyenangkan untuk ditulis.
"""

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


# --------------------------------------------------------- bilah formatnya ---


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
    """Tombol yang menulis tanda yang ditolak pengurai adalah tombol yang
    menghasilkan galat, bukan format."""
    assert f'depan: "{markah}"' in BILAH, f"{nama} menulis tanda yang lain"


@pytest.mark.parametrize("huruf", ["b", "i", "k"])
def test_pintasan_papan_tik_yang_sudah_dihafal_orang(huruf):
    assert f"{huruf}: {{ depan:" in BILAH, f"Ctrl+{huruf.upper()} tidak terpasang"


def test_pintasan_dipasang_pada_kotaknya_bukan_pada_dokumen():
    """Ctrl+B di kolom judul tidak boleh diam diam menulis bintang."""
    assert "el.addEventListener" in BILAH
    assert "document.addEventListener" not in BILAH


def test_tumpukan_urung_peramban_tidak_dibuang():
    """Menyetel value langsung membuang tumpukan urung, sehingga Ctrl+Z
    sesudah menekan Tebal membatalkan seluruh paragraf yang baru diketik.
    Urung yang membatalkan hal yang salah lebih buruk daripada tidak ada."""
    assert 'execCommand("insertText"' in BILAH
    # Dan tetap ada jalan mundurnya kalau execCommand tidak ada.
    assert "if (!berhasil)" in BILAH


# ----------------------------------------------------------- pratinjaunya ---


def test_pratinjau_dibangun_server_bukan_pengurai_kedua_di_peramban():
    assert "pratinjauTulisan" in PENYUNTING
    assert "/api/v1/admin/pratinjau" in API


@pytest.mark.parametrize("tanda", ["**", "## ", "](", "blockquote"])
def test_tidak_ada_pengurai_markah_kedua_di_penyunting(tanda):
    """Dua pengurai untuk satu bahasa markah akan berpisah. Yang berpisah
    diam diam membuat pratinjau mengatakan tulisannya baik, lalu Simpan
    menolaknya dengan alasan yang tidak pernah terlihat di pratinjau.

    Yang boleh ada di penyunting cuma pemecah blok kasar untuk menghitung
    paragraf, dan itu tidak menghasilkan HTML sama sekali.
    """
    # Tanda markah boleh muncul di BilahFormat, sebab di sana ia ditulis,
    # bukan diurai. Yang dijaga penyuntingnya sendiri.
    hasil = re.findall(r"replace\(.*" + re.escape(tanda), PENYUNTING)
    assert hasil == [], f"ada yang mengurai {tanda!r} sendiri di penyunting"


def test_pratinjau_tidak_dibersihkan_lagi_di_peramban():
    """Membersihkan lagi berarti dua aturan untuk satu hal, dan dua aturan
    akan berpisah. Yang menjaganya pengurai di server, yang meng-escape
    seluruh teks dan menolak HTML mentah dengan galat."""
    assert "dangerouslySetInnerHTML" in PENYUNTING
    assert "DOMPurify" not in PENYUNTING and "sanitize" not in PENYUNTING


# ------------------------------------------------------- sisipan medianya ---


def test_media_disisipkan_ke_kedua_bahasa_sekaligus():
    """Dua bahasa wajib sebangun blok demi blok, jadi gambar yang hanya masuk
    ke satu bahasa langsung membuat tulisannya ditolak."""
    assert "[kotakEn.current, kotakId.current]" in PENYUNTING


@pytest.mark.parametrize("bentuk", ['"!video[]("', '"![]("'])
def test_bentuk_sisipan_sama_dengan_yang_diterima_pengurai(bentuk):
    assert bentuk in PENYUNTING


# ----------------------------------------------------------- unggahannya ---


def test_layar_unggah_menyebut_soal_lokasi_di_dalam_foto():
    """Foto dari ponsel bisa membawa koordinat tempat pemotretannya, dan
    koordinat itu ikut terbit. Yang mengunggah foto anaknya di rumah tidak
    akan membuka dokumentasi lebih dulu, jadi kalimatnya harus di layar.

    Sejak 19 September 2026 ada kotak centang untuk membuangnya. Peringatannya
    tetap wajib ada, sebab kotaknya mati secara bawaan: yang tidak
    mencentangnya harus tahu apa yang ia biarkan ikut terbit.
    """
    assert "koordinat" in PUSTAKA
    assert "tidak dibuang" in PUSTAKA
    assert 'id="buang-metadata"' in PUSTAKA, "tidak ada kotak centangnya"
    assert "buangMetadata" in PUSTAKA


def test_kotak_buang_metadata_mati_secara_bawaan():
    """Yang tahu apakah tempatnya boleh diketahui umum adalah pemiliknya.
    Membuang secara bawaan berarti memutuskan untuknya, dan sebagian foto
    memang justru perlu lokasinya."""
    assert "useState(false);" in PUSTAKA.split("buangMetadata")[1][:40], (
        "kotak buang metadata tidak mati secara bawaan"
    )


def test_layar_unggah_menyebut_jenis_yang_tidak_bisa_dibuang():
    """Membuang setengah lalu mengaku sudah bersih lebih berbahaya daripada
    tidak membuang sama sekali."""
    assert "GIF dan AVIF" in PUSTAKA


def test_jenis_yang_ditawarkan_peramban_sama_dengan_yang_diterima_server():
    """Menawarkan jenis yang akan ditolak server berarti menyuruh orang
    menunggu unggahan delapan puluh megabita selesai untuk sebuah penolakan
    yang sudah pasti sejak awal."""
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
    """fetch belum bisa melaporkan berapa bita yang sudah terkirim. Untuk
    video di sambungan rumahan, bilah yang bergerak adalah beda antara
    menunggu dan mengira aplikasinya menggantung."""
    assert "XMLHttpRequest" in API
    assert "upload.onprogress" in API


def test_content_type_tidak_dipasang_tangan_untuk_multipart():
    """Peramban menuliskannya sendiri beserta boundary-nya, dan boundary yang
    ditulis tangan hampir selalu salah."""
    potong = API[API.index("function sekaliUnggah"):API.index("export async function unggahBerkas")]
    assert "Content-Type" not in potong


def test_unggahan_diulang_sekali_kalau_tokennya_mati_di_tengah_jalan():
    """Access token berumur 15 menit. Video besar bisa melewatinya di tengah
    jalan, dan tanpa pengulangan yang hilang unggahan yang sudah sembilan
    puluh persen terkirim."""
    potong = API[API.index("export async function unggahBerkas"):]
    assert "auth/refresh" in potong[:1500]


# ------------------------------------------------------------ dua portnya ---


def test_port_next_mengenal_jenis_blok_yang_sama_dengan_pengurainya():
    """Port yang mengenal lebih sedikit jenis daripada pengurainya akan
    menerbitkan halaman yang kehilangan satu gambar tanpa satu pun galat.

    Yang dibandingkan daftar jenis di tools/markah.py dengan union Block di
    next/content/posts.ts. Keduanya ditulis tangan di tempat berbeda, dan
    salinan sistem yang kedua sudah pernah tertinggal berhari hari.
    """
    posts = (AKAR / "next" / "content" / "posts.ts").read_text(encoding="utf-8")
    markah_py = (AKAR / "tools" / "markah.py").read_text(encoding="utf-8")

    di_next = set(re.findall(r'\{ kind: "([a-z0-9]+)"', posts))

    # Jenis yang benar benar bisa keluar dari blok(), dibaca dari baris yang
    # membentuk Blok, bukan dari komentar.
    di_pengurai = set(re.findall(r'Blok\(\s*"([a-z0-9]+)"', markah_py))
    di_pengurai |= set(re.findall(r'\(\s*(?:BUTIR_UL|BUTIR_OL|VIDEO|GAMBAR),\s*"([a-z0-9]+)"\)', markah_py))
    # Kutipan dan paragraf tidak dibentuk lewat Blok(...) langsung: keduanya
    # mengumpulkan barisnya dulu, dan jenisnya disetel ke variabel.
    di_pengurai |= set(re.findall(r'jenis(?:, mulai)? = "([a-z0-9]+)"', markah_py))

    assert di_next == di_pengurai, (
        f"hanya di port Next: {sorted(di_next - di_pengurai)}, "
        f"hanya di pengurai: {sorted(di_pengurai - di_next)}"
    )


@pytest.mark.parametrize("jenis", ["ul", "ol", "gambar", "video"])
def test_port_next_benar_benar_menggambar_jenis_barunya(jenis):
    """Tipe yang ada di union tetapi tidak ada cabangnya di komponen akan
    jatuh ke cabang terakhir dan terbit sebagai paragraf kosong."""
    tampilan = (AKAR / "next" / "components" / "PostView.tsx").read_text(encoding="utf-8")
    assert f'block.kind === "{jenis}"' in tampilan, f"{jenis} tidak digambar port Next"
