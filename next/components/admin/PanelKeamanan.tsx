"use client";

import { useCallback, useEffect, useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import { KameraWajah } from "@/components/admin/KameraWajah";
import {
  aktifkanTotp,
  daftarkanWajah,
  GagalApi,
  hapusWajah,
  keadaanKeamanan,
  kirimVerifikasiEmail,
  konfirmasiEmail,
  matikanTotp,
  mulaiTotp,
  peristiwaKeamanan,
  type KeadaanKeamanan,
  type Peristiwa,
} from "@/lib/api";

/**
 * Panel keamanan akun.
 *
 * Tiga hal yang membentuk isinya, dan semuanya soal berterus terang:
 *
 * 1. **Keadaan yang sebenarnya ditampilkan, termasuk yang belum siap.** Kalau
 *    SMTP belum dikonfigurasi, tombol kirim tetap ada tetapi disertai
 *    keterangan bahwa suratnya akan ditulis ke berkas dan tidak berangkat.
 *    Tombol yang diam diam gagal jauh lebih buruk daripada tombol yang
 *    menjelaskan kenapa ia belum bisa dipakai.
 * 2. **Kode pemulihan ditampilkan sekali.** Setelah panel ini ditutup, tidak
 *    ada siapa pun yang bisa menunjukkannya lagi, sebab yang tersimpan di
 *    server cuma sidiknya. Itu dikatakan di layar, bukan diasumsikan dimengerti.
 * 3. **Yang gagal ikut ditampilkan di jejaknya.** Daftar yang hanya memuat
 *    keberhasilan cuma memberi tahu pemiliknya apa yang sudah ia lakukan.
 *    Yang gagal memberi tahu bahwa ada orang lain sedang mencoba.
 */

const NAMA_PERISTIWA: Record<string, string> = {
  masuk: "Masuk",
  sandi_benar: "Sandi benar, menunggu faktor kedua",
  otp_dikirim: "Kode dikirim ke email",
  otp_salah: "Kode email salah",
  totp_salah: "Kode authenticator salah",
  totp_aktifkan: "Authenticator dinyalakan",
  totp_matikan: "Authenticator dimatikan",
  kode_pemulihan: "Kode pemulihan dipakai",
  verifikasi_email: "Verifikasi email",
  verifikasi_email_dikirim: "Tautan verifikasi dikirim",
  wajah_daftar: "Wajah didaftarkan",
  wajah_hapus: "Wajah dihapus",
  wajah_cocok: "Wajah cocok",
  wajah_salah: "Wajah tidak cocok",
};

function waktu(nilai: string): string {
  try {
    return new Intl.DateTimeFormat("id-ID", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Asia/Jakarta",
    }).format(new Date(nilai));
  } catch {
    return nilai;
  }
}

export function PanelKeamanan() {
  const [keadaan, setKeadaan] = useState<KeadaanKeamanan | null>(null);
  const [jejak, setJejak] = useState<Peristiwa[]>([]);
  const [galat, setGalat] = useState("");
  const [kabar, setKabar] = useState("");
  const [sibuk, setSibuk] = useState(false);

  /* Pemasangan TOTP yang sedang berjalan. */
  const [pasang, setPasang] = useState<{ rahasia: string; qr: string; otpauth: string } | null>(null);
  const [kode, setKode] = useState("");
  const [pemulihan, setPemulihan] = useState<string[] | null>(null);
  const [kodeMatikan, setKodeMatikan] = useState("");
  const [kameraHidup, setKameraHidup] = useState(false);

  const muat = useCallback(async () => {
    try {
      const [k, p] = await Promise.all([keadaanKeamanan(), peristiwaKeamanan()]);
      setKeadaan(k);
      setJejak(p.peristiwa);
    } catch (e) {
      setGalat(e instanceof GagalApi ? e.message : "gagal memuat keadaan keamanan");
    }
  }, []);

  useEffect(() => {
    void muat();
  }, [muat]);

  /* Tautan verifikasi dibuka dari kotak surat, dan mendarat di /admin dengan
     ?verifikasi=... di alamatnya. Ditangani di sini lalu dihapus dari alamat,
     supaya tokennya tidak tertinggal di riwayat peramban. */
  useEffect(() => {
    const alamat = new URL(window.location.href);
    const token = alamat.searchParams.get("verifikasi");
    if (!token) return;
    alamat.searchParams.delete("verifikasi");
    window.history.replaceState(null, "", alamat.toString());
    konfirmasiEmail(token)
      .then(() => {
        setKabar("Email Anda sudah terbukti.");
        void muat();
      })
      .catch((e) => setGalat(e instanceof GagalApi ? e.message : "tautan tidak berlaku"));
  }, [muat]);

  function bersihkan() {
    setGalat("");
    setKabar("");
  }

  async function jalankan(kerja: () => Promise<void>) {
    bersihkan();
    setSibuk(true);
    try {
      await kerja();
    } catch (e) {
      setGalat(e instanceof GagalApi ? e.message : "gagal menghubungi server");
    } finally {
      setSibuk(false);
    }
  }

  if (!keadaan) {
    return (
      <section className={gaya.kartu}>
        <p className={gaya.ket}>Sebentar...</p>
      </section>
    );
  }

  return (
    <section className={gaya.kartu}>
      <div className={gaya.tumpuk}>
        <h2>Keamanan akun</h2>
        <span className={gaya.kanan}>
          <button type="button" className={gaya.tombol} onClick={() => void muat()} disabled={sibuk}>
            Muat ulang
          </button>
        </span>
      </div>

      {galat ? (
        <p className={`${gaya.kabar} ${gaya.salah}`} role="alert">
          {galat}
        </p>
      ) : null}
      {kabar ? (
        <p className={`${gaya.kabar} ${gaya.baik}`} role="status">
          {kabar}
        </p>
      ) : null}

      {/* ------------------------------------------------ ringkasan */}

      <ul className={gaya.daftarKeadaan}>
        <li>
          <span className={`${gaya.tanda} ${keadaan.email_terverifikasi ? gaya.terbit : ""}`}>
            {keadaan.email_terverifikasi ? "terbukti" : "belum"}
          </span>
          <span>Email {keadaan.email}</span>
        </li>
        <li>
          <span className={`${gaya.tanda} ${keadaan.totp_aktif ? gaya.terbit : ""}`}>
            {keadaan.totp_aktif ? "aktif" : "belum"}
          </span>
          <span>Aplikasi authenticator</span>
        </li>
        <li>
          <span className={`${gaya.tanda} ${keadaan.passkey > 0 ? gaya.terbit : ""}`}>
            {keadaan.passkey}
          </span>
          <span>Sidik jari dan passkey</span>
        </li>
        <li>
          <span className={`${gaya.tanda} ${keadaan.pemulihan_sisa > 0 ? gaya.terbit : ""}`}>
            {keadaan.pemulihan_sisa}
          </span>
          <span>Kode pemulihan yang tersisa</span>
        </li>
        <li>
          <span className={`${gaya.tanda} ${keadaan.wajah_terdaftar ? gaya.terbit : ""}`}>
            {keadaan.wajah_terdaftar ? "aktif" : "belum"}
          </span>
          <span>Verifikasi wajah</span>
        </li>
      </ul>

      {/* ------------------------------------------- verifikasi email */}

      <h3 className={gaya.subjudul}>Email</h3>
      <p className={gaya.penjelasan}>
        Buktikan alamat email Anda. Ini yang dipakai kalau suatu saat Anda perlu masuk
        kembali. Selama belum terbukti, kode masuk lewat email belum bisa dipakai.
      </p>
      {!keadaan.surat_siap ? (
        <p className={`${gaya.kabar} ${gaya.salah}`}>
          Email belum bisa dikirim. Suratnya disimpan di <code>cadangan/surat/</code>, tidak
          sampai ke mana pun. Isi SMTP_HOST, SMTP_PENGGUNA, SMTP_SANDI, dan SURAT_DARI di{" "}
          <code>.env</code>.
        </p>
      ) : null}
      <div className={gaya.aksi}>
        <button
          type="button"
          className={gaya.tombol}
          disabled={sibuk}
          onClick={() =>
            jalankan(async () => {
              const hasil = await kirimVerifikasiEmail();
              setKabar(hasil.terkirim ? "Tautan sudah dikirim ke email Anda." : hasil.catatan);
            })
          }
        >
          {keadaan.email_terverifikasi ? "Kirim ulang tautan" : "Kirim tautan"}
        </button>
      </div>

      {/* --------------------------------------------------- TOTP */}

      <h3 className={gaya.subjudul}>Aplikasi authenticator</h3>
      <p className={gaya.penjelasan}>
        Kode enam angka yang berganti tiap 30 detik. Dihitung di ponsel Anda, tanpa
        internet, jadi tidak ada surat yang bisa dibaca orang lain. Pakai Aegis, Google
        Authenticator, atau 1Password.
      </p>

      {!keadaan.kunci_kolom_siap ? (
        <p className={`${gaya.kabar} ${gaya.salah}`}>
          Belum bisa dipasang. Isi KUNCI_KOLOM di <code>.env</code> dulu, buat kuncinya
          dengan <code>python backend/db/enkripsi.py kunci</code>. Tanpa itu rahasia
          authenticator akan tersimpan polos, dan itu tidak saya lakukan.
        </p>
      ) : null}

      {pemulihan ? (
        <div className={gaya.pemulihan}>
          <p className={gaya.penjelasan}>
            <strong>Simpan delapan kode ini sekarang.</strong> Kode ini cuma muncul sekali
            dan tidak bisa dilihat lagi. Kalau ponsel Anda hilang, ini jalan masuk Anda.
            Simpan bukan di ponsel yang sama.
          </p>
          <ul className={gaya.kodeGrid}>
            {pemulihan.map((k) => (
              <li key={k}>
                <code>{k}</code>
              </li>
            ))}
          </ul>
          <button type="button" className={gaya.tombol} onClick={() => setPemulihan(null)}>
            Sudah saya simpan
          </button>
        </div>
      ) : keadaan.totp_aktif ? (
        <>
          <p className={gaya.penjelasan}>
            Sedang aktif. Masukkan kode dari aplikasi untuk mematikannya. Kode pemulihan
            Anda ikut terhapus.
          </p>
          <div className={gaya.baris}>
            <label htmlFor="kode-matikan">Kode dari aplikasi</label>
            <input
              id="kode-matikan"
              className={`${gaya.isian} ${gaya.kodeIsian}`}
              inputMode="numeric"
              autoComplete="one-time-code"
              value={kodeMatikan}
              onChange={(e) => setKodeMatikan(e.target.value)}
              placeholder="000000"
            />
          </div>
          <div className={gaya.aksi}>
            <button
              type="button"
              className={`${gaya.tombol} ${gaya.bahaya}`}
              disabled={sibuk || kodeMatikan.trim().length < 6}
              onClick={() =>
                jalankan(async () => {
                  await matikanTotp(kodeMatikan.trim());
                  setKodeMatikan("");
                  setKabar("Authenticator dimatikan. Kode pemulihan ikut terhapus.");
                  await muat();
                })
              }
            >
              Matikan authenticator
            </button>
          </div>
        </>
      ) : pasang ? (
        <>
          <p className={gaya.penjelasan}>
            Pindai kode ini dengan aplikasi authenticator Anda, lalu ketik enam angka yang
            muncul.
          </p>
          <div
            className={gaya.qr}
            /* SVG-nya datang dari API situs ini sendiri dan isinya dibangkitkan
               dari matriks hitam putih, bukan dari masukan pengguna. Tidak ada
               jalan bagi teks siapa pun untuk sampai ke sini. */
            dangerouslySetInnerHTML={{ __html: pasang.qr }}
          />
          <p className={gaya.penjelasan}>
            Tidak bisa memindai? Ketik kunci ini: <code>{pasang.rahasia}</code>
          </p>
          <div className={gaya.baris}>
            <label htmlFor="kode-totp">Enam angka dari aplikasi</label>
            <input
              id="kode-totp"
              className={`${gaya.isian} ${gaya.kodeIsian}`}
              inputMode="numeric"
              autoComplete="one-time-code"
              value={kode}
              onChange={(e) => setKode(e.target.value)}
              placeholder="000000"
            />
          </div>
          <div className={gaya.aksi}>
            <button
              type="button"
              className={`${gaya.tombol} ${gaya.utama}`}
              disabled={sibuk || kode.trim().length < 6}
              onClick={() =>
                jalankan(async () => {
                  const hasil = await aktifkanTotp(kode.trim());
                  setPemulihan(hasil.kode_pemulihan);
                  setPasang(null);
                  setKode("");
                  await muat();
                })
              }
            >
              Aktifkan
            </button>
            <button type="button" className={gaya.tombol} onClick={() => setPasang(null)}>
              Batal
            </button>
          </div>
        </>
      ) : (
        <div className={gaya.aksi}>
          <button
            type="button"
            className={gaya.tombol}
            disabled={sibuk || !keadaan.kunci_kolom_siap}
            onClick={() =>
              jalankan(async () => {
                const hasil = await mulaiTotp();
                setPasang(hasil as { rahasia: string; qr: string; otpauth: string });
              })
            }
          >
            Pasang authenticator
          </button>
        </div>
      )}

      {/* --------------------------------------------------- wajah */}

      <h3 className={gaya.subjudul}>Verifikasi wajah</h3>
      <p className={gaya.penjelasan}>
        Saat masuk, kamera minta tiga foto mengikuti gerakan yang diminta. Fotonya{" "}
        <strong>tidak disimpan</strong>. Yang disimpan cuma 128 angka, dan angka itu pun
        dikunci.
      </p>
      <p className={gaya.penjelasan}>
        <strong>Perlu Anda tahu:</strong> ini bisa ditembus rekaman video wajah Anda.
        Gunanya mempersulit orang yang sudah tahu sandi Anda, bukan menutup pintu. Yang
        paling aman tetap sidik jari.
      </p>

      {!keadaan.wajah_siap ? (
        <p className={`${gaya.kabar} ${gaya.salah}`}>
          Belum bisa dipakai. Jalankan <code>python tools/ambil_model.py</code> di server,
          37 MB, sekali saja. Selama belum, verifikasi wajah tidak ditawarkan saat masuk.
        </p>
      ) : null}

      {kameraHidup ? (
        <KameraWajah
          gerakan={["tengah", "kiri", "kanan"]}
          sibuk={sibuk}
          batal={() => setKameraHidup(false)}
          selesai={(bingkai) => {
            setKameraHidup(false);
            void jalankan(async () => {
              await daftarkanWajah(bingkai);
              setKabar("Wajah Anda terdaftar. Fotonya tidak disimpan.");
              await muat();
            });
          }}
        />
      ) : (
        <div className={gaya.aksi}>
          {keadaan.wajah_terdaftar ? (
            <button
              type="button"
              className={`${gaya.tombol} ${gaya.bahaya}`}
              disabled={sibuk}
              onClick={() =>
                jalankan(async () => {
                  await hapusWajah();
                  setKabar("Wajah dihapus dari server.");
                  await muat();
                })
              }
            >
              Hapus wajah
            </button>
          ) : (
            <button
              type="button"
              className={gaya.tombol}
              disabled={sibuk || !keadaan.wajah_siap || !keadaan.kunci_kolom_siap}
              onClick={() => {
                bersihkan();
                setKameraHidup(true);
              }}
            >
              Daftarkan wajah
            </button>
          )}
        </div>
      )}

      {/* ----------------------------------------------- jejak */}

      <h3 className={gaya.subjudul}>Aktivitas terakhir</h3>
      <p className={gaya.penjelasan}>
        Yang gagal ikut dicatat. Kalau ada orang lain mencoba masuk, Anda lihat di sini.
        Alamat IP tidak disimpan, hanya ringkasannya.
      </p>
      {jejak.length === 0 ? (
        <p className={gaya.ket}>Belum ada catatan.</p>
      ) : (
        <div className={gaya.tabelBungkus}>
          <table>
            <thead>
              <tr>
                <th>Waktu</th>
                <th>Peristiwa</th>
                <th>Hasil</th>
                <th>Keterangan</th>
              </tr>
            </thead>
            <tbody>
              {jejak.map((p, i) => (
                <tr key={`${p.pada}-${i}`}>
                  <td>{waktu(p.pada)}</td>
                  <td>{NAMA_PERISTIWA[p.jenis] ?? p.jenis}</td>
                  <td>
                    <span className={`${gaya.tanda} ${p.berhasil ? gaya.terbit : gaya.gagal}`}>
                      {p.berhasil ? "berhasil" : "gagal"}
                    </span>
                  </td>
                  <td>{p.keterangan ?? "tidak ada"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
