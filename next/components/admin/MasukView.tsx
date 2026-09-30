"use client";

import { useEffect, useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import { BrandMark } from "@/components/Icons";
import { Kabar, baik, buruk, type IsiKabar } from "@/components/admin/Kabar";
import { KameraWajah } from "@/components/admin/KameraWajah";
import {
  GagalApi,
  kirimUlangKode,
  masukSandi,
  pesanDari,
  selesaikanFaktorKedua,
  tantanganWajah,
  type CaraFaktorKedua,
  type Sesi,
  type TantanganWajah,
} from "@/lib/api";
import * as passkey from "@/lib/passkey";

const NAMA_CARA: Record<CaraFaktorKedua, string> = {
  totp: "Aplikasi authenticator",
  email: "Kode yang dikirim ke email",
  pemulihan: "Kode cadangan",
  wajah: "Verifikasi wajah, akses terbatas",
};

const PETUNJUK: Record<CaraFaktorKedua, string> = {
  totp: "Buka aplikasi authenticator, lalu ketik 6 angka yang muncul.",
  email: "Kami sudah kirim 6 angka ke email kamu. Berlaku 10 menit.",
  pemulihan: "Pakai salah satu kode cadangan yang kamu simpan. Tiap kode sekali pakai.",
  wajah:
    "Kamera ambil 3 foto sambil kamu menoleh. Lewat wajah kamu cuma bisa melihat. Menulis dan mengubah keamanan tetap butuh authenticator.",
};

const WAJAH_GAGAL =
  "Wajah belum bisa dipastikan. Ikuti arah toleh di layar, lalu coba lagi di tempat yang lebih terang.";

type Tiket = { nilai: string; cara: CaraFaktorKedua[] };

function IkonMata() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M1.8 12S5.4 5.5 12 5.5 22.2 12 22.2 12 18.6 18.5 12 18.5 1.8 12 1.8 12z" />
      <circle cx="12" cy="12" r="3.2" />
      <path className={gaya.coret} d="M4 20 20 4" />
    </svg>
  );
}

export function MasukView({
  sesudah,
  hanyaKuat = false,
}: {
  sesudah: (s: Sesi) => void;
  hanyaKuat?: boolean;
}) {
  const [email, setEmail] = useState("");
  const [sandi, setSandi] = useState("");
  const [sandiTerlihat, setSandiTerlihat] = useState(false);
  const [kabar, setKabar] = useState<IsiKabar>(null);
  const [sibuk, setSibuk] = useState(false);
  const [adaPasskey, setAdaPasskey] = useState(false);
  const [halangan, setHalangan] = useState<passkey.Kendala | null>(null);

  const [tiket, setTiket] = useState<Tiket | null>(null);
  const [cara, setCara] = useState<CaraFaktorKedua>("totp");
  const [kode, setKode] = useState("");
  const [tantangan, setTantangan] = useState<TantanganWajah | null>(null);

  useEffect(() => {
    let batal = false;
    setHalangan(passkey.kendala());
    passkey.siap().then((ya) => {
      if (!batal) setAdaPasskey(ya);
    });
    return () => {
      batal = true;
    };
  }, []);

  async function jalankan(kerja: () => Promise<void>, gagal = pesanDari) {
    setKabar(null);
    setSibuk(true);
    try {
      await kerja();
    } catch (e) {
      setKabar(buruk(gagal(e)));
    } finally {
      setSibuk(false);
    }
  }

  function kembali() {
    setTiket(null);
    setKode("");
    setTantangan(null);
    setKabar(null);
  }

  function gantiCara(baru: CaraFaktorKedua) {
    setCara(baru);
    setKode("");
    setTantangan(null);
    setKabar(null);
  }

  function denganSandi(event: React.FormEvent) {
    event.preventDefault();
    void jalankan(async () => {
      const hasil = await masukSandi(email.trim(), sandi);
      setSandi("");
      setSandiTerlihat(false);
      if (hasil.tahap === "faktor2") {
        const kuat = hasil.cara.filter((c) => c !== "wajah");
        const pilihan = hanyaKuat && kuat.length ? kuat : hasil.cara;
        setTiket({ nilai: hasil.tiket, cara: pilihan });
        setCara(pilihan[0]);
        return;
      }
      sesudah(hasil);
    });
  }

  function denganKode(event: React.FormEvent) {
    event.preventDefault();
    if (!tiket) return;
    void jalankan(async () => {
      try {
        sesudah(await selesaikanFaktorKedua(tiket.nilai, cara, kode.trim()));
      } catch (e) {
        setKode("");
        throw e;
      }
    });
  }

  function kirimUlang() {
    if (!tiket) return;
    void jalankan(async () => {
      const hasil = await kirimUlangKode(tiket.nilai);
      setKabar(hasil.terkirim ? baik("Kode baru sudah dikirim.") : buruk(hasil.catatan));
    });
  }

  function mulaiWajah() {
    if (!tiket) return;
    void jalankan(async () => setTantangan(await tantanganWajah(tiket.nilai)));
  }

  function kirimWajah(bingkai: string[]) {
    if (!tiket || !tantangan) return;
    const { tantangan: id } = tantangan;
    setTantangan(null);
    void jalankan(
      async () => sesudah(await selesaikanFaktorKedua(tiket.nilai, "wajah", "", { tantangan: id, bingkai })),
      (e) => (e instanceof GagalApi && e.status === 429 ? e.message : WAJAH_GAGAL),
    );
  }

  async function denganPasskey() {
    const kendala = passkey.kendala();
    if (kendala) {
      setHalangan(kendala);
      setKabar(buruk(kendala.saran ? `${kendala.pesan} Buka ${kendala.saran}` : kendala.pesan));
      return;
    }

    setKabar(null);
    setSibuk(true);
    try {
      sesudah(await passkey.masuk());
    } catch (e) {
      if (passkey.dibatalkan(e)) return;
      if ((e as { name?: string })?.name === "SecurityError") {
        const lagi = passkey.kendala();
        setKabar(
          buruk(
            lagi?.saran
              ? `${lagi.pesan} Buka ${lagi.saran}`
              : "Alamat halaman ini tidak bisa dipakai untuk sidik jari.",
          ),
        );
        return;
      }
      setKabar(buruk(pesanDari(e, "Masuk pakai sidik jari gagal.")));
    } finally {
      setSibuk(false);
    }
  }

  const kepala = (
    <div className={gaya.masukKepala}>
      <BrandMark size={40} />
      <div>
        <h1>{tiket ? "Satu langkah lagi" : "Masuk"}</h1>
        <p>hendrokuswantoro.com</p>
      </div>
    </div>
  );

  const kaki = (
    <a className={gaya.masukKaki} href="/">
      &larr; Kembali ke situs
    </a>
  );

  if (tiket) {
    const pakaiKode = cara !== "wajah";
    return (
      <div className={gaya.masukBungkus}>
        <section className={`${gaya.kartu} ${gaya.masuk}`}>
          {kepala}
          <Kabar isi={kabar} />

          <p className={gaya.penjelasan}>Sandi kamu benar. Tinggal satu langkah lagi, waktunya 5 menit.</p>

          {hanyaKuat && !tiket.cara.includes("wajah") ? (
            <p className={gaya.penjelasan}>
              Wajah tidak ditawarkan di sini. Lewat wajah, tulisan dan keamanan tetap terkunci.
            </p>
          ) : null}

          {tiket.cara.length > 1 ? (
            <div className={gaya.baris}>
              <label htmlFor="cara">Cara</label>
              <select
                id="cara"
                className={gaya.isian}
                value={cara}
                onChange={(e) => gantiCara(e.target.value as CaraFaktorKedua)}
              >
                {tiket.cara.map((c) => (
                  <option key={c} value={c}>
                    {NAMA_CARA[c]}
                  </option>
                ))}
              </select>
            </div>
          ) : null}

          <p className={gaya.penjelasan}>{PETUNJUK[cara]}</p>

          {pakaiKode ? (
            <form onSubmit={denganKode}>
              <div className={gaya.baris}>
                <label htmlFor="kode">{cara === "pemulihan" ? "Kode cadangan" : "Kode 6 angka"}</label>
                <input
                  id="kode"
                  className={`${gaya.isian} ${gaya.kodeIsian}`}
                  inputMode={cara === "pemulihan" ? "text" : "numeric"}
                  autoComplete={cara === "pemulihan" ? "off" : "one-time-code"}
                  autoFocus
                  required
                  value={kode}
                  onChange={(e) => setKode(e.target.value)}
                  placeholder={cara === "pemulihan" ? "XXXXX-XXXXX" : "000000"}
                />
              </div>
              <button
                type="submit"
                className={`${gaya.tombol} ${gaya.utama} ${gaya.lebar}`}
                disabled={sibuk || kode.trim().length < 4}
              >
                {sibuk ? "Sebentar..." : "Lanjutkan"}
              </button>
            </form>
          ) : (
            <button
              type="button"
              className={`${gaya.tombol} ${gaya.utama} ${gaya.lebar}`}
              onClick={mulaiWajah}
              disabled={sibuk}
            >
              {sibuk ? "Sebentar..." : "Nyalakan kamera"}
            </button>
          )}

          <div className={gaya.masukBawah}>
            <button type="button" className={`${gaya.tombol} ${gaya.kecil} ${gaya.hantu}`} onClick={kembali}>
              &larr; Kembali
            </button>
            {cara === "email" ? (
              <button
                type="button"
                className={`${gaya.tombol} ${gaya.kecil}`}
                onClick={kirimUlang}
                disabled={sibuk}
              >
                Kirim ulang kode
              </button>
            ) : null}
          </div>

          {tantangan ? (
            <KameraWajah
              gerakan={tantangan.gerakan}
              sibuk={sibuk}
              batal={() => setTantangan(null)}
              selesai={kirimWajah}
            />
          ) : null}
        </section>
        {kaki}
      </div>
    );
  }

  return (
    <div className={gaya.masukBungkus}>
      <section className={`${gaya.kartu} ${gaya.masuk}`}>
        {kepala}
        <Kabar isi={kabar} />

        {adaPasskey ? (
          <>
            <button
              type="button"
              className={`${gaya.tombol} ${gaya.utama} ${gaya.lebar}`}
              onClick={denganPasskey}
              disabled={sibuk || halangan !== null}
            >
              Masuk pakai sidik jari
            </button>
            <p className={`${gaya.penjelasan} ${gaya.diBawahTombol}`}>
              {halangan ? (
                <>
                  {halangan.pesan}{" "}
                  {halangan.saran ? (
                    <>
                      Buka <a href={halangan.saran}>{halangan.saran}</a>.
                    </>
                  ) : null}
                </>
              ) : (
                "Perangkat kamu yang minta sidik jari, wajah, atau PIN. Sidik jari kamu tidak dikirim ke mana pun."
              )}
            </p>
            <div className={gaya.pisah}>atau dengan sandi</div>
          </>
        ) : null}

        <form onSubmit={denganSandi}>
          <div className={gaya.baris}>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              className={gaya.isian}
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className={gaya.baris}>
            <label htmlFor="sandi">Sandi</label>
            <div className={gaya.sandiBidang}>
              <input
                id="sandi"
                className={gaya.isian}
                type={sandiTerlihat ? "text" : "password"}
                autoComplete="current-password"
                required
                minLength={8}
                value={sandi}
                onChange={(e) => setSandi(e.target.value)}
              />
              <button
                type="button"
                className={gaya.lihat}
                aria-controls="sandi"
                aria-pressed={sandiTerlihat}
                aria-label={sandiTerlihat ? "Sembunyikan sandi" : "Tampilkan sandi"}
                title={sandiTerlihat ? "Sembunyikan sandi" : "Tampilkan sandi"}
                onClick={() => setSandiTerlihat((t) => !t)}
              >
                <IkonMata />
              </button>
            </div>
          </div>

          <button
            type="submit"
            className={`${gaya.tombol} ${adaPasskey ? "" : gaya.utama} ${gaya.lebar}`}
            disabled={sibuk}
          >
            {sibuk ? "Sebentar..." : "Masuk"}
          </button>
        </form>
      </section>
      {kaki}
    </div>
  );
}
