"use client";

import { HOME } from "@/content/home";
import { useLang } from "./LanguageProvider";

const TITIK: Array<[number, number]> = [
  [72, 318], [160, 214], [250, 250], [318, 118], [410, 140], [500, 262], [570, 150],
];
const PIN = "M0 0s-11-10-11-18a11 11 0 0 1 22 0c0 8-11 18-11 18z";

export function PetaKecil() {
  const { say } = useLang();

  return (
    <figure className="ajak-peta__gambar reveal" aria-hidden="true">
      <svg viewBox="0 0 640 400" focusable="false">
        <rect width="640" height="400" fill="#111111" />
        <g fill="none" stroke="#ffffff" strokeOpacity="0.09" strokeWidth="1.2">
          <path d="M40 300c60-70 150-90 230-60s150 40 230-20 110-60 140-50" />
          <path d="M20 250c70-60 160-80 250-50s140 30 220-30 120-70 160-60" />
          <path d="M30 200c80-50 170-60 250-40s130 20 210-40 110-60 150-60" />
          <path d="M60 150c70-40 150-50 230-30s120 10 190-40 100-50 140-50" />
          <path d="M110 100c60-30 130-40 190-20s110 10 170-30 90-40 120-40" />
          <path d="M40 350c70-50 160-60 240-40s160 40 240-10 90-40 120-40" />
        </g>
        <path
          d="M72 318C150 260 190 300 250 250s80-120 160-110 120 60 160 10"
          fill="none"
          stroke="#276ef1"
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray="2 12"
        />
        <circle className="gelombang" cx="410" cy="140" r="12" fill="none" stroke="#276ef1" strokeWidth="2" />
        <g fill="#ffffff">
          {TITIK.map(([x, y], i) => (
            <g key={i} transform={`translate(${x} ${y})`}>
              <path className="titik" d={PIN} fill={i === 4 ? "#276ef1" : undefined} />
            </g>
          ))}
        </g>
        <g transform="translate(28 28)">
          <rect width="148" height="64" rx="12" fill="#ffffff" />
          <text x="16" y="26" fontFamily="Poppins, sans-serif" fontSize="12" fontWeight="500" fill="#6b6b6b">
            {say(HOME.mapPins)}
          </text>
          <text x="16" y="50" fontFamily="Poppins, sans-serif" fontSize="20" fontWeight="700" fill="#000000">
            {TITIK.length}
          </text>
        </g>
      </svg>
    </figure>
  );
}
