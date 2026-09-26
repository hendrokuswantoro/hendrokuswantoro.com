"use client";

import { useCallback, useEffect, useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import { ambil, panggil } from "@/lib/api";
import * as passkey from "@/lib/passkey";
import { BarisSetelan } from "@/components/admin/Setelan";

export function PanelPasskey() {
  const [daftar, setDaftar] = useState<passkey.Kunci[] | null>(null);
  const [kabar, setKabar] = useState<{ teks: string; baik: boolean } | null>(null);
  const [bisa, setBisa] = useState(false);
  const [halangan, setHalangan] = useState<passkey.Kendala | null>(null);

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
    passkey.siap().then((ya) => {
      if (batal) return;
      setBisa(ya);
      if (ya) void muat();
    });
    return () => {
      batal = true;
    };
  }, [muat]);

  if (!bisa) return null;

  async function daftarkan(jenis: "perangkat" | "kunci") {
    const bawaan = jenis === "perangkat" ? "Laptop kerja" : "Kunci USB";
    const h = passkey.kendala();
    if (h) {
      setHalangan(h);
      setKabar({ teks: h.saran ? `${h.pesan} Buka ${h.saran}` : h.pesan, baik: false });
      return;
    }
    const nama = window.prompt("Kasih nama perangkat ini", bawaan);
    if (nama === null) return;
    setKabar(null);
    try {
      await passkey.daftarkan(nama, jenis);
      setKabar({ teks: "Perangkat berhasil didaftarkan.", baik: true });
      await muat();
    } catch (e) {
      if (passkey.dibatalkan(e)) return;
      const nama_galat = (e as { name?: string })?.name;
      setKabar({
        teks:
          nama_galat === "InvalidStateError"
            ? "perangkat ini sudah terdaftar"
            : e instanceof Error
              ? e.message
              : "pendaftaran gagal",
        baik: false,
      });
    }
  }

  async function cabut(kunci: passkey.Kunci) {
    if (
      !window.confirm(
        `Cabut "${kunci.nama}"? Perangkat ini tidak bisa dipakai masuk lagi.`,
      )
    ) {
      return;
    }
    const jawaban = await panggil(`/api/v1/auth/passkey/${encodeURIComponent(kunci.id)}`, {
      method: "DELETE",
    });
    if (!jawaban.ok) {
      setKabar({ teks: "Gagal mencabut. Coba lagi.", baik: false });
      return;
    }
    setKabar({ teks: "Perangkat sudah dicabut.", baik: true });
    await muat();
  }

  const jumlah = daftar?.length ?? 0;

  return (
    <BarisSetelan
      ikon="sidik"
      judul="Sidik jari dan passkey"
      sub={daftar === null ? "Memuat..." : jumlah ? `${jumlah} perangkat` : "Belum ada"}
      tanda={jumlah ? "aktif" : "belum"}
      baik={jumlah > 0}
    >
      <p className={gaya.penjelasan}>
        Cara masuk paling aman. Sidik jari kamu tetap di perangkat, tidak dikirim ke mana
        pun. Halaman palsu juga tidak bisa memintanya.
      </p>
      <p className={gaya.penjelasan}>
        Daftarkan dua perangkat, biar kamu tetap bisa masuk kalau satu hilang.
      </p>

      {halangan ? (
        <p className={gaya.penjelasan}>
          {halangan.pesan}{" "}
          {halangan.saran ? (
            <>
              Buka <a href={halangan.saran}>{halangan.saran}</a>.
            </>
          ) : null}
        </p>
      ) : null}

      {kabar ? (
        <p className={`${gaya.kabar} ${kabar.baik ? gaya.baik : gaya.salah}`} role="status">
          {kabar.teks}
        </p>
      ) : null}

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
                onClick={() => cabut(k)}
              >
                Cabut
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      <div className={gaya.aksi}>
        <button
          type="button"
          className={`${gaya.tombol} ${gaya.kecil} ${gaya.utama}`}
          onClick={() => void daftarkan("perangkat")}
          disabled={halangan !== null}
        >
          Daftarkan sidik jari
        </button>
        <button
          type="button"
          className={`${gaya.tombol} ${gaya.kecil}`}
          onClick={() => void daftarkan("kunci")}
          disabled={halangan !== null}
        >
          Pakai kunci USB
        </button>
      </div>
    </BarisSetelan>
  );
}
