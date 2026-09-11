import type { CoverKind } from "@/content/projects";

/** Flat SVG covers, one per project. Green only, no photography needed. */
export function ProjectCover({ kind }: { kind: CoverKind }) {
  switch (kind) {
    case "parking":
      return (
        <svg viewBox="0 0 400 225" aria-hidden="true">
          <rect width="400" height="225" fill="#00730d" />
          <g stroke="#ffffff" strokeOpacity="0.2" strokeWidth="2">
            <path d="M0 70h400M0 140h400M100 0v225M260 0v225" />
          </g>
          <path d="M20 180C90 150 120 92 200 92s110 58 180 30" fill="none" stroke="#00aa13" strokeWidth="7" strokeLinecap="round" />
          <g fill="#ffffff">
            <circle cx="120" cy="118" r="6" />
            <circle cx="200" cy="92" r="6" />
            <circle cx="288" cy="104" r="6" />
          </g>
        </svg>
      );
    case "fire":
      return (
        <svg viewBox="0 0 400 225" aria-hidden="true">
          <rect width="400" height="225" fill="#005c0a" />
          <g fill="#00aa13">
            <circle cx="88" cy="150" r="34" />
            <circle cx="150" cy="96" r="22" />
            <circle cx="232" cy="132" r="44" />
            <circle cx="316" cy="80" r="26" />
          </g>
          <g fill="#9be0a6">
            <circle cx="88" cy="150" r="10" />
            <circle cx="232" cy="132" r="12" />
            <circle cx="316" cy="80" r="8" />
          </g>
        </svg>
      );
    case "fish":
      return (
        <svg viewBox="0 0 400 225" aria-hidden="true">
          <rect width="400" height="225" fill="#00730d" />
          <path d="M0 150c60-26 96 14 152-4s84-58 152-44c40 8 72 34 96 30v93H0Z" fill="#005c0a" />
          <path d="M0 168c58-22 104 16 160-2s88-46 152-32c36 8 64 28 88 26" fill="none" stroke="#9be0a6" strokeWidth="5" />
          <g fill="#ffffff">
            <rect x="248" y="52" width="16" height="16" rx="4" />
            <rect x="276" y="72" width="16" height="16" rx="4" />
            <rect x="220" y="80" width="16" height="16" rx="4" />
          </g>
        </svg>
      );
    case "reach":
      return (
        <svg viewBox="0 0 400 225" aria-hidden="true">
          <rect width="400" height="225" fill="#005c0a" />
          <g fill="none" stroke="#00aa13" strokeWidth="3">
            <circle cx="200" cy="112" r="30" />
            <circle cx="200" cy="112" r="58" />
            <circle cx="200" cy="112" r="86" />
          </g>
          <path d="M40 196c54-30 78-84 160-84s106 44 160 22" fill="none" stroke="#9be0a6" strokeWidth="5" strokeLinecap="round" />
          <circle cx="200" cy="112" r="9" fill="#ffffff" />
        </svg>
      );
    case "landcover":
      return (
        <svg viewBox="0 0 400 225" aria-hidden="true">
          <rect width="400" height="225" fill="#005c0a" />
          <g fill="#00aa13">
            <path d="M0 0h150v92H0Z" />
            <path d="M150 0h130v60H150Z" />
          </g>
          <g fill="#9be0a6">
            <path d="M0 92h96v133H0Z" />
            <path d="M280 0h120v120H280Z" />
          </g>
          <g fill="#ffffff" fillOpacity="0.35">
            <path d="M96 92h184v133H96Z" />
            <path d="M280 120h120v105H280Z" />
          </g>
        </svg>
      );
    case "sheet":
      return (
        <svg viewBox="0 0 400 225" aria-hidden="true">
          <rect width="400" height="225" fill="#00730d" />
          <g stroke="#ffffff" strokeOpacity="0.22" strokeWidth="1">
            <path d="M0 45h400M0 90h400M0 135h400M0 180h400M80 0v225M160 0v225M240 0v225M320 0v225" />
          </g>
          <path d="M60 40h180v145H60Z" fill="none" stroke="#9be0a6" strokeWidth="4" />
          <path d="M60 40 240 185M240 40 60 185" stroke="#00aa13" strokeWidth="3" />
          <rect x="270" y="40" width="70" height="145" rx="8" fill="#ffffff" />
          <g fill="#00730d">
            <rect x="284" y="58" width="42" height="8" rx="4" />
            <rect x="284" y="78" width="42" height="8" rx="4" />
            <rect x="284" y="98" width="28" height="8" rx="4" />
          </g>
        </svg>
      );
    default:
      return null;
  }
}
