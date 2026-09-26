"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import gaya from "@/app/admin/admin.module.css";

const JUDUL: Record<string, string> = {
  tengah: "Hadap lurus ke kamera",
  kiri: "Toleh ke kiri",
  kanan: "Toleh ke kanan",
};

export function KameraWajah({
  gerakan,
  selesai,
  batal,
  sibuk = false,
}: {
  gerakan: string[];
  selesai: (bingkai: string[]) => void;
  batal: () => void;
  sibuk?: boolean;
}) {
  const video = useRef<HTMLVideoElement | null>(null);
  const arus = useRef<MediaStream | null>(null);
  const [galat, setGalat] = useState("");
  const [hidup, setHidup] = useState(false);
  const [diambil, setDiambil] = useState<string[]>([]);

  const matikan = useCallback(() => {
    arus.current?.getTracks().forEach((t) => t.stop());
    arus.current = null;
    setHidup(false);
  }, []);

  useEffect(() => {
    let batalkan = false;

    async function nyalakan() {
      if (!navigator.mediaDevices?.getUserMedia) {
        setGalat("Peramban ini tidak bisa memakai kamera.");
        return;
      }
      try {
        const media = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
          audio: false,
        });
        if (batalkan) {
          media.getTracks().forEach((t) => t.stop());
          return;
        }
        arus.current = media;
        if (video.current) {
          video.current.srcObject = media;
          await video.current.play().catch(() => undefined);
        }
        setHidup(true);
      } catch (e) {
        const nama = (e as { name?: string })?.name;
        setGalat(
          nama === "NotAllowedError"
            ? "Kamera belum diizinkan. Izinkan di peramban Anda, lalu coba lagi."
            : nama === "NotFoundError"
              ? "Tidak ada kamera di perangkat ini."
              : "Kamera tidak bisa dinyalakan.",
        );
      }
    }

    void nyalakan();
    return () => {
      batalkan = true;
      matikan();
    };
  }, [matikan]);

  function ambil() {
    const el = video.current;
    if (!el || !el.videoWidth) return;

    const kanvas = document.createElement("canvas");
    kanvas.width = el.videoWidth;
    kanvas.height = el.videoHeight;
    const konteks = kanvas.getContext("2d");
    if (!konteks) return;
    konteks.drawImage(el, 0, 0);

    const berikut = [...diambil, kanvas.toDataURL("image/jpeg", 0.85)];
    setDiambil(berikut);

    if (berikut.length === gerakan.length) {
      matikan();
      selesai(berikut);
    }
  }

  const sekarang = gerakan[diambil.length];

  return (
    <div className={gaya.kamera}>
      {galat ? (
        <p className={`${gaya.kabar} ${gaya.salah}`} role="alert">
          {galat}
        </p>
      ) : null}

      <div className={gaya.kameraBingkai}>
        <video ref={video} muted playsInline className={gaya.kameraVideo} />
        {sekarang ? (
          <div className={gaya.kameraArah}>
            <span>{JUDUL[sekarang] ?? sekarang}</span>
            <small>
              foto {diambil.length + 1} dari {gerakan.length}
            </small>
          </div>
        ) : null}
      </div>

      <div className={gaya.aksi}>
        <button
          type="button"
          className={`${gaya.tombol} ${gaya.utama}`}
          onClick={ambil}
          disabled={!hidup || sibuk || !sekarang}
        >
          {sibuk ? "Sebentar..." : "Ambil foto"}
        </button>
        <button
          type="button"
          className={gaya.tombol}
          onClick={() => {
            matikan();
            batal();
          }}
        >
          Batal
        </button>
      </div>
    </div>
  );
}
