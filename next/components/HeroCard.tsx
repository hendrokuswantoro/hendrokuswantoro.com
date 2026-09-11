"use client";

import { HOME } from "@/content/home";
import { useLang } from "./LanguageProvider";

export function HeroCard() {
  const { say } = useLang();

  return (
    <figure className="hero__card reveal">
      <svg viewBox="0 0 640 420" role="img" aria-label={say(HOME.cardAlt)}>
        <rect width="640" height="420" fill="#00730d" />
        <g stroke="#ffffff" strokeOpacity="0.12" strokeWidth="1">
          <path d="M0 60h640M0 120h640M0 180h640M0 240h640M0 300h640M0 360h640" />
          <path d="M80 0v420M160 0v420M240 0v420M320 0v420M400 0v420M480 0v420M560 0v420" />
        </g>
        <g fill="#ffffff" fillOpacity="0.08">
          <rect x="52" y="86" width="118" height="72" rx="10" />
          <rect x="205" y="62" width="86" height="110" rx="10" />
          <rect x="352" y="96" width="140" height="64" rx="10" />
          <rect x="84" y="228" width="150" height="92" rx="10" />
          <rect x="290" y="252" width="104" height="68" rx="10" />
          <rect x="440" y="220" width="132" height="122" rx="10" />
        </g>
        <path
          d="M-10 330c90-18 132-96 224-104 92-8 128 62 214 46 62-12 96-62 222-46"
          fill="none"
          stroke="#00aa13"
          strokeWidth="10"
          strokeLinecap="round"
        />
        <path
          d="M60 386C140 300 176 268 258 252c82-16 120 26 186-10 48-26 72-74 138-96"
          fill="none"
          stroke="#9be0a6"
          strokeWidth="4"
          strokeDasharray="14 10"
          strokeLinecap="round"
        />
        <g>
          <circle cx="258" cy="252" r="9" fill="#ffffff" />
          <circle cx="258" cy="252" r="18" fill="none" stroke="#ffffff" strokeOpacity="0.45" strokeWidth="2" />
          <circle cx="444" cy="242" r="7" fill="#9be0a6" />
          <circle cx="120" cy="330" r="7" fill="#9be0a6" />
        </g>
        <g transform="translate(384 40)">
          <rect width="212" height="96" rx="16" fill="#ffffff" />
          <text x="20" y="34" fontFamily="var(--font-inter), sans-serif" fontSize="13" fontWeight="600" fill="#6b7178">
            {say(HOME.cardPoints)}
          </text>
          <text x="20" y="70" fontFamily="var(--font-outfit), sans-serif" fontSize="30" fontWeight="700" fill="#00730d">
            UTM 49S
          </text>
        </g>
      </svg>
      <figcaption>
        <span className="pulse">
          <i />
          <span>{say(HOME.cardLive)}</span>
        </span>
        <span>{say(HOME.cardStack)}</span>
      </figcaption>
    </figure>
  );
}
