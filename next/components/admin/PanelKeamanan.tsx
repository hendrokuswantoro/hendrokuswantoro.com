"use client";

import { useCallback, useEffect, useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import { KameraWajah } from "@/components/admin/KameraWajah";
import { PanelPasskey } from "@/components/admin/PanelPasskey";
import { Kabar, baik, buruk, type IsiKabar } from "@/components/admin/Kabar";
import { BarisSetelan, Terkunci } from "@/components/admin/Setelan";
import type { Akses } from "@/components/admin/akses";
import {
  aktifkanTotp,
  daftarkanWajah,
  hapusWajah,
  kirimVerifikasiEmail,
  konfirmasiEmail,
  matikanTotp,
  mulaiTotp,
  peristiwaKeamanan,
  pesanDari,
  type KeadaanKeamanan,
  type Peristiwa,
} from "@/lib/api";

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

export function PanelKeamanan({
  keadaan,
  galatKeadaan,
  akses,
  muatKeadaan,
}: {
  keadaan: KeadaanKeamanan | null;
  galatKeadaan: string;
  akses: Akses;
  muatKeadaan: () => Promise<void>;
}) {
  const [jejak, setJejak] = useState<Peristiwa[]>([]);
  const [kabar, setKabar] = useState<IsiKabar>(null);
  const [sibuk, setSibuk] = useState(false);

  const [pasang, setPasang] = useState<{ rahasia: string; qr: string; otpauth: string } | null>(null);
  const [kode, setKode] = useState("");
  const [pemulihan, setPemulihan] = useState<string[] | null>(null);
  const [kodeMatikan, setKodeMatikan] = useState("");
  const [kameraHidup, setKameraHidup] = useState(false);

  const muatJejak = useCallback(async () => {
    try {
      setJejak((await peristiwaKeamanan()).peristiwa);
    } catch (e) {
      setKabar(buruk(pesanDari(e, "Aktivitas gagal dimuat.")));
    }
  }, []);

  const muat = useCallback(
    () => Promise.all([muatKeadaan(), muatJejak()]).then(() => undefined),
    [muatKeadaan, muatJejak],
  );

  useEffect(() => {
    void muatJejak();
  }, [muatJejak]);

  useEffect(() => {
    const alamat = new URL(window.location.href);
    const fragmen = new URLSearchParams(alamat.hash.slice(1));
    const token = fragmen.get("verifikasi") || alamat.searchParams.get("verifikasi");
    if (!token) return;
    alamat.searchParams.delete("verifikasi");
    alamat.hash = "";
    window.history.replaceState(null, "", alamat.toString());
    konfirmasiEmail(token)
      .then(() => {
        setKabar(baik("Email kamu sudah terbukti."));
        void muat();
      })
      .catch((e) => setKabar(buruk(pesanDari(e, "Tautan tidak berlaku."))));
  }, [muat]);

  async function jalankan(kerja: () => Promise<void>) {
    setKabar(null);
    setSibuk(true);
    try {
      await kerja();
    } catch (e) {
      setKabar(buruk(pesanDari(e)));
    } finally {
      setSibuk(false);
    }
  }

  if (!keadaan) {
    return (
      <section className={gaya.kartu} id="keamanan">
        {galatKeadaan ? <Kabar isi={buruk(galatKeadaan)} /> : <p className={gaya.ket}>Sebentar...</p>}
      </section>
    );
  }

  const kuat = akses.penuh;
  const daftar = akses.bolehMendaftar;

  const gagalTerakhir = jejak.filter((p) => !p.berhasil).length;

  return (
    <section className={gaya.kartu} id="keamanan" aria-labelledby="judul-keamanan">
      <div className={gaya.tumpuk}>
        <h2 id="judul-keamanan">Keamanan akun</h2>
        <span className={gaya.kanan}>
          <button
            type="button"
            className={`${gaya.tombol} ${gaya.kecil}`}
            onClick={() => void muat()}
            disabled={sibuk}
          >
            Muat ulang
          </button>
        </span>
      </div>

      <Kabar isi={kabar} />

      <ul className={gaya.setelan}>
        <BarisSetelan
          ikon="surat"
          judul="Email"
          sub={keadaan.email}
          tanda={keadaan.email_terverifikasi ? "terbukti" : "belum"}
          baik={keadaan.email_terverifikasi}
        >
          <p className={gaya.penjelasan}>
            Email ini dipakai buat bantu kamu masuk kalau cara lain tidak bisa. Buktikan
            dulu lewat tautan yang kami kirim.
          </p>
          {!keadaan.surat_siap ? (
            <p className={`${gaya.kabar} ${gaya.salah}`}>
              Email belum bisa dikirim. Isi SMTP_HOST, SMTP_PENGGUNA, SMTP_SANDI, dan
              SURAT_DARI di <code>.env</code> dulu. Sementara itu suratnya disimpan di{" "}
              <code>cadangan/surat/</code>.
            </p>
          ) : null}
          <div className={gaya.aksi}>
            <button
              type="button"
              className={`${gaya.tombol} ${gaya.kecil}`}
              disabled={sibuk}
              onClick={() =>
                jalankan(async () => {
                  const hasil = await kirimVerifikasiEmail();
                  setKabar(hasil.terkirim ? baik("Tautan sudah dikirim. Cek email kamu.") : buruk(hasil.catatan));
                })
              }
            >
              {keadaan.email_terverifikasi ? "Kirim ulang tautan" : "Kirim tautan"}
            </button>
          </div>
        </BarisSetelan>

        <BarisSetelan
          ikon="ponsel"
          judul="Aplikasi authenticator"
          sub={
            keadaan.totp_aktif
              ? `Aktif, ${keadaan.pemulihan_sisa} kode cadangan tersisa`
              : "Belum dipasang"
          }
          tanda={keadaan.totp_aktif ? "aktif" : "belum"}
          baik={keadaan.totp_aktif}
        >
          {!keadaan.kunci_kolom_siap ? (
            <p className={`${gaya.kabar} ${gaya.salah}`}>
              Belum bisa dipasang. Isi KUNCI_KOLOM di <code>.env</code> dulu. Buat kuncinya
              dengan <code>python backend/db/enkripsi.py kunci</code>.
            </p>
          ) : null}

          {pemulihan ? (
            <div className={gaya.pemulihan}>
              <p className={gaya.penjelasan}>
                <strong>Simpan 8 kode ini sekarang.</strong> Kodenya cuma muncul sekali. Pakai
                kalau HP kamu hilang, dan simpan di tempat selain HP itu.
              </p>
              <ul className={gaya.kodeGrid}>
                {pemulihan.map((k) => (
                  <li key={k}>
                    <code>{k}</code>
                  </li>
                ))}
              </ul>
              <button
                type="button"
                className={`${gaya.tombol} ${gaya.kecil}`}
                onClick={() => setPemulihan(null)}
              >
                Sudah saya simpan
              </button>
            </div>
          ) : keadaan.totp_aktif ? (
            <>
              <p className={gaya.penjelasan}>
                Sudah aktif. Mau matikan? Ketik kode dari aplikasi. Kode cadangan ikut
                terhapus.
              </p>
              {!kuat ? <Terkunci /> : null}
              <div className={gaya.barisSebaris}>
                <input
                  id="kode-matikan"
                  aria-label="Kode dari aplikasi"
                  className={`${gaya.isian} ${gaya.kodeIsian}`}
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  value={kodeMatikan}
                  onChange={(e) => setKodeMatikan(e.target.value)}
                  placeholder="000000"
                />
                <button
                  type="button"
                  className={`${gaya.tombol} ${gaya.kecil} ${gaya.bahaya}`}
                  disabled={sibuk || !kuat || kodeMatikan.trim().length < 6}
                  onClick={() =>
                    jalankan(async () => {
                      await matikanTotp(kodeMatikan.trim());
                      setKodeMatikan("");
                      setKabar(baik("Authenticator dimatikan. Kode cadangan ikut terhapus."));
                      await muat();
                    })
                  }
                >
                  Matikan
                </button>
              </div>
            </>
          ) : pasang ? (
            <>
              <p className={gaya.penjelasan}>
                Pindai kode ini pakai aplikasi authenticator, lalu ketik 6 angkanya.
              </p>
              <div className={gaya.qr} dangerouslySetInnerHTML={{ __html: pasang.qr }} />
              <p className={gaya.ket}>
                Tidak bisa memindai? Ketik kode ini: <code>{pasang.rahasia}</code>
              </p>
              <div className={gaya.barisSebaris}>
                <input
                  id="kode-totp"
                  aria-label="Enam angka dari aplikasi"
                  className={`${gaya.isian} ${gaya.kodeIsian}`}
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  value={kode}
                  onChange={(e) => setKode(e.target.value)}
                  placeholder="000000"
                />
                <button
                  type="button"
                  className={`${gaya.tombol} ${gaya.kecil} ${gaya.utama}`}
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
                <button
                  type="button"
                  className={`${gaya.tombol} ${gaya.kecil}`}
                  onClick={() => setPasang(null)}
                >
                  Batal
                </button>
              </div>
            </>
          ) : (
            <>
              <p className={gaya.penjelasan}>
                Kode 6 angka dari aplikasi di HP kamu, berganti tiap 30 detik. Bisa pakai
                Aegis, Google Authenticator, atau 1Password.
              </p>
              {!daftar ? <Terkunci /> : null}
              <div className={gaya.aksi}>
                <button
                  type="button"
                  className={`${gaya.tombol} ${gaya.kecil} ${gaya.utama}`}
                  disabled={sibuk || !daftar || !keadaan.kunci_kolom_siap}
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
            </>
          )}
        </BarisSetelan>

        <PanelPasskey akses={akses} onBerubah={muatKeadaan} />

        <BarisSetelan
          ikon="wajah"
          judul="Verifikasi wajah"
          sub={keadaan.wajah_terdaftar ? "Aktif" : "Belum didaftarkan"}
          tanda={keadaan.wajah_terdaftar ? "aktif" : "belum"}
          baik={keadaan.wajah_terdaftar}
        >
          <p className={gaya.penjelasan}>
            Kamera ambil 3 foto sambil kamu menoleh. Fotonya <strong>tidak disimpan</strong>,
            cuma 128 angka yang dikunci.
          </p>
          <p className={gaya.penjelasan}>
            <strong>Perlu kamu tahu:</strong> cara ini bisa ditembus rekaman video wajah
            kamu. Yang paling aman tetap sidik jari.
          </p>

          {!keadaan.wajah_siap ? (
            <p className={`${gaya.kabar} ${gaya.salah}`}>
              Belum bisa dipakai. Jalankan <code>python tools/ambil_model.py</code> di server
              dulu, sekali saja.
            </p>
          ) : null}

          {(keadaan.wajah_terdaftar ? !kuat : !daftar) ? <Terkunci /> : null}

          <div className={gaya.aksi}>
            {keadaan.wajah_terdaftar ? (
              <button
                type="button"
                className={`${gaya.tombol} ${gaya.kecil} ${gaya.bahaya}`}
                disabled={sibuk || !kuat}
                onClick={() =>
                  jalankan(async () => {
                    await hapusWajah();
                    setKabar(baik("Wajah sudah dihapus dari server."));
                    await muat();
                  })
                }
              >
                Hapus wajah
              </button>
            ) : (
              <button
                type="button"
                className={`${gaya.tombol} ${gaya.kecil} ${gaya.utama}`}
                disabled={sibuk || !daftar || !keadaan.wajah_siap || !keadaan.kunci_kolom_siap}
                onClick={() => {
                  setKabar(null);
                  setKameraHidup(true);
                }}
              >
                Daftarkan wajah
              </button>
            )}
          </div>
        </BarisSetelan>

        <BarisSetelan
          ikon="jam"
          judul="Aktivitas terakhir"
          sub={
            jejak.length === 0
              ? "Belum ada catatan"
              : gagalTerakhir
                ? `${jejak.length} catatan, ${gagalTerakhir} gagal`
                : `${jejak.length} catatan, semua berhasil`
          }
        >
          <p className={gaya.penjelasan}>
            Percobaan yang gagal juga dicatat, jadi kamu tahu kalau ada orang lain mencoba
            masuk. Alamat IP tidak disimpan.
          </p>
          {jejak.length === 0 ? null : (
            <ul className={gaya.daftarRingkas}>
              {jejak.map((p, i) => (
                <li key={`${p.pada}-${i}`}>
                  <span>
                    <strong>{NAMA_PERISTIWA[p.jenis] ?? p.jenis}</strong>
                    <small>
                      {waktu(p.pada)}
                      {p.keterangan ? `, ${p.keterangan}` : ""}
                    </small>
                  </span>
                  <span className={`${gaya.tanda} ${p.berhasil ? gaya.terbit : gaya.gagal}`}>
                    {p.berhasil ? "berhasil" : "gagal"}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </BarisSetelan>
      </ul>

      {kameraHidup ? (
        <KameraWajah
          gerakan={["tengah", "kiri", "kanan"]}
          sibuk={sibuk}
          batal={() => setKameraHidup(false)}
          selesai={(bingkai) => {
            setKameraHidup(false);
            void jalankan(async () => {
              await daftarkanWajah(bingkai);
              setKabar(baik("Wajah kamu terdaftar. Fotonya tidak disimpan."));
              await muat();
            });
          }}
        />
      ) : null}
    </section>
  );
}
