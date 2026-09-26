"use client";

import { useCallback, useEffect, useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import { ambil, panggil, pesanDari, pesanGalat } from "@/lib/api";
import * as passkey from "@/lib/passkey";
import { Kabar, baik, buruk, type IsiKabar } from "@/components/admin/Kabar";
import { BarisSetelan, Terkunci } from "@/components/admin/Setelan";
import type { Akses } from "@/components/admin/akses";

export function PanelPasskey({
  akses,
  onBerubah,
}: {
  akses: Akses;
  onBerubah: () => Promise<void>;
}) {
  const [daftar, setDaftar] = useState<passkey.Kunci[] | null>(null);
  const [kabar, setKabar] = useState<IsiKabar>(null);
  const [bisa, setBisa] = useState<boolean | null>(null);
  const [halangan, setHalangan] = useState<passkey.Kendala | null>(null);
  const [nama, setNama] = useState("");
  const [sibuk, setSibuk] = useState(false);
  const [lokal, setLokal] = useState(false);

  const muat = useCallback(async () => {
    try {
      const jawaban = await ambil<{ daftar: passkey.Kunci[] }>("/api/v1/auth/passkey");
      setDaftar(jawaban.daftar);
    } catch {
      setDaftar([]);
    }
  }, []);

  useEffect(() => {
    let batal = false;
    setHalangan(passkey.kendala());
    setLokal(window.location.hostname === "localhost");
    passkey.siap().then((ya) => {
      if (batal) return;
      setBisa(ya);
      if (ya) void muat();
    });
    return () => {
      batal = true;
    };
  }, [muat]);

  async function daftarkan(jenis: "perangkat" | "kunci") {
    const h = passkey.kendala();
    if (h) {
      setHalangan(h);
      setKabar(buruk(h.saran ? `${h.pesan} Buka ${h.saran}` : h.pesan));
      return;
    }
    const label = nama.trim() || (jenis === "perangkat" ? "Laptop ini" : "Kunci USB");
    setKabar(null);
    setSibuk(true);
    try {
      await passkey.daftarkan(label, jenis);
      setNama("");
      setKabar(baik(`${label} berhasil didaftarkan.`));
      await Promise.all([muat(), onBerubah()]);
    } catch (e) {
      if (passkey.dibatalkan(e)) return;
      const sudahAda = (e as { name?: string })?.name === "InvalidStateError";
      setKabar(buruk(sudahAda ? "Perangkat ini sudah terdaftar." : pesanDari(e, "Pendaftaran gagal. Coba lagi.")));
    } finally {
      setSibuk(false);
    }
  }

  async function cabut(kunci: passkey.Kunci) {
    if (!window.confirm(`Cabut "${kunci.nama}"? Perangkat ini tidak bisa dipakai masuk lagi.`)) {
      return;
    }
    setSibuk(true);
    try {
      const jawaban = await panggil(`/api/v1/auth/passkey/${encodeURIComponent(kunci.id)}`, {
        method: "DELETE",
      });
      if (!jawaban.ok) {
        setKabar(buruk(pesanGalat(await jawaban.json().catch(() => null))));
        return;
      }
      setKabar(baik(`${kunci.nama} sudah dicabut.`));
      await Promise.all([muat(), onBerubah()]);
    } finally {
      setSibuk(false);
    }
  }

  const jumlah = daftar?.length ?? 0;
  const bolehDaftar = akses.bolehMendaftar && halangan === null && !sibuk;

  return (
    <BarisSetelan
      ikon="sidik"
      judul="Sidik jari dan passkey"
      sub={
        bisa === false
          ? "Belum bisa dipakai di server ini"
          : daftar === null
            ? "Memuat..."
            : jumlah
              ? `${jumlah} perangkat`
              : "Belum ada perangkat"
      }
      tanda={jumlah ? "aktif" : "belum"}
      baik={jumlah > 0}
    >
      <p className={gaya.penjelasan}>
        Cara masuk paling aman. Sidik jari kamu tetap di perangkat, tidak dikirim ke mana
        pun. Halaman palsu juga tidak bisa memintanya.
      </p>

      {bisa === false ? (
        <p className={`${gaya.kabar} ${gaya.salah}`}>
          Server belum siap untuk passkey. Isi WEBAUTHN_RP_ID dan WEBAUTHN_ASAL di{" "}
          <code>.env</code>, lalu nyalakan ulang servernya.
        </p>
      ) : (
        <>
          <p className={gaya.penjelasan}>
            Daftarkan dua perangkat, biar kamu tetap bisa masuk kalau satu hilang.
          </p>
          {lokal ? (
            <p className={gaya.ket}>
              Yang didaftarkan di sini cuma berlaku di localhost. Di situs sungguhan nanti,
              daftarkan lagi.
            </p>
          ) : null}

          {halangan ? (
            <p className={`${gaya.kabar} ${gaya.salah}`}>
              {halangan.pesan}{" "}
              {halangan.saran ? (
                <>
                  Buka <a href={halangan.saran}>{halangan.saran}</a>.
                </>
              ) : null}
            </p>
          ) : null}

          <Kabar isi={kabar} />

          {daftar && daftar.length ? (
            <ul className={gaya.daftarRingkas}>
              {daftar.map((k) => (
                <li key={k.id}>
                  <span>
                    <strong>{k.nama}</strong>
                    <small>
                      {k.dipakai_pada
                        ? `Terakhir dipakai ${k.dipakai_pada.slice(0, 10)}`
                        : "Belum pernah dipakai"}
                    </small>
                  </span>
                  <button
                    type="button"
                    className={`${gaya.tombol} ${gaya.kecil} ${gaya.bahaya}`}
                    onClick={() => void cabut(k)}
                    disabled={!akses.penuh || sibuk}
                  >
                    Cabut
                  </button>
                </li>
              ))}
            </ul>
          ) : null}

          {!akses.bolehMendaftar ? <Terkunci /> : null}

          <div className={gaya.barisSebaris}>
            <input
              className={`${gaya.isian} ${gaya.isianNama}`}
              aria-label="Nama perangkat"
              placeholder="Nama, misalnya Laptop kerja"
              value={nama}
              maxLength={60}
              onChange={(e) => setNama(e.target.value)}
              disabled={!bolehDaftar}
            />
            <button
              type="button"
              className={`${gaya.tombol} ${gaya.kecil} ${gaya.utama}`}
              onClick={() => void daftarkan("perangkat")}
              disabled={!bolehDaftar}
            >
              {sibuk ? "Sebentar..." : "Daftarkan sidik jari"}
            </button>
            <button
              type="button"
              className={`${gaya.tombol} ${gaya.kecil}`}
              onClick={() => void daftarkan("kunci")}
              disabled={!bolehDaftar}
            >
              Pakai kunci USB
            </button>
          </div>
        </>
      )}
    </BarisSetelan>
  );
}
