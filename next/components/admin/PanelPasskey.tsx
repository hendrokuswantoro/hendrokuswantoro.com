"use client";

import { useCallback, useEffect, useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import { ambil, panggil } from "@/lib/api";
import * as passkey from "@/lib/passkey";

export function PanelPasskey() {
  const [daftar, setDaftar] = useState<passkey.Kunci[] | null>(null);
  const [kabar, setKabar] = useState<{ teks: string; baik: boolean } | null>(null);
  const [bisa, setBisa] = useState(false);

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
    const nama = window.prompt("Beri nama perangkat ini", bawaan);
    if (nama === null) return;
    setKabar(null);
    try {
      await passkey.daftarkan(nama, jenis);
      setKabar({ teks: "Perangkat terdaftar.", baik: true });
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
        `Cabut "${kunci.nama}"? Perangkat itu tidak bisa dipakai masuk lagi.`,
      )
    ) {
      return;
    }
    const jawaban = await panggil(`/api/v1/auth/passkey/${encodeURIComponent(kunci.id)}`, {
      method: "DELETE",
    });
    if (!jawaban.ok) {
      setKabar({ teks: "gagal mencabut", baik: false });
      return;
    }
    setKabar({ teks: "passkey dicabut", baik: true });
    await muat();
  }

  return (
    <section className={gaya.kartu}>
      <div className={gaya.tumpuk}>
        <h2>Sidik jari dan passkey</h2>
        <div className={gaya.kanan}>
          <button
            type="button"
            className={`${gaya.tombol} ${gaya.utama}`}
            onClick={() => void daftarkan("perangkat")}
          >
            Daftarkan sidik jari
          </button>
          <button type="button" className={gaya.tombol} onClick={() => void daftarkan("kunci")}>
            Daftarkan kunci USB
          </button>
        </div>
      </div>

      <p className={gaya.penjelasan}>
        Cara masuk paling aman di sini. Kuncinya tersimpan di perangkat Anda dan terikat
        pada alamat situs ini, jadi halaman palsu tidak bisa memintanya.
      </p>

      <p className={gaya.penjelasan}>
        Sidik jari Anda tidak dikirim ke mana pun. Perangkat Anda yang memeriksanya. Di
        perangkat tanpa sensor, yang diminta PIN perangkat itu.
      </p>

      <p className={gaya.penjelasan}>
        Daftarkan lebih dari satu perangkat. Kalau cuma satu dan perangkatnya hilang, Anda
        terkunci di luar.
      </p>

      {kabar ? (
        <p className={`${gaya.kabar} ${kabar.baik ? gaya.baik : gaya.salah}`} role="status">
          {kabar.teks}
        </p>
      ) : null}

      {daftar === null ? (
        <p className={gaya.ket}>Memuat...</p>
      ) : daftar.length === 0 ? (
        <p className={gaya.ket}>
          Belum ada. Sekarang masuk masih pakai sandi.
        </p>
      ) : (
        <div className={gaya.tabelBungkus}>
          <table>
            <thead>
              <tr>
                <th>Nama</th>
                <th>Jenis</th>
                <th>Terakhir dipakai</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {daftar.map((k) => (
                <tr key={k.id}>
                  <td>{k.nama}</td>
                  <td>{k.jenis_perangkat === "multi_device" ? "tersinkron" : "satu perangkat"}</td>
                  <td>{k.dipakai_pada ? k.dipakai_pada.slice(0, 10) : "belum pernah"}</td>
                  <td>
                    <button
                      type="button"
                      className={`${gaya.tombol} ${gaya.bahaya}`}
                      onClick={() => cabut(k)}
                    >
                      Cabut
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
