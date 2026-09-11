/**
 * Inline icons. Stroke icons inherit `currentColor` so the stylesheet keeps
 * control of their colour, exactly as in the plain HTML version.
 */
const stroke = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
  focusable: "false" as const,
};

export function BrandMark({ size = 34 }: { size?: number }) {
  return (
    <svg className="brand__mark" width={size} height={size} viewBox="0 0 48 48" aria-hidden="true" focusable="false">
      <rect width="48" height="48" rx="15" fill="#008a10" />
      <path d="M15 33V15h4.6v6.7h8.8V15H33v18h-4.6v-7.2h-8.8V33z" fill="#fff" />
      <circle cx="37.5" cy="11.5" r="3.5" fill="#9be0a6" />
    </svg>
  );
}

export function GlobeIcon() {
  return (
    <svg viewBox="0 0 24 24" {...stroke}>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3a15 15 0 0 1 0 18 15 15 0 0 1 0-18Z" />
    </svg>
  );
}

export function ChartIcon() {
  return (
    <svg viewBox="0 0 24 24" {...stroke}>
      <path d="M3 3v18h18" />
      <path d="m7 15 4-5 3 3 5-7" />
    </svg>
  );
}

export function SatelliteIcon() {
  return (
    <svg viewBox="0 0 24 24" {...stroke}>
      <path d="M2 12a10 10 0 0 1 10-10" />
      <path d="M6 12a6 6 0 0 1 6-6" />
      <circle cx="12" cy="12" r="2" />
      <path d="M12 18v3M9 21h6" />
    </svg>
  );
}

export function MapIcon() {
  return (
    <svg viewBox="0 0 24 24" {...stroke}>
      <path d="m9 4 6 2 5.4-1.8a.7.7 0 0 1 .9.7v13.4l-6.3 2.1-6-2-5.4 1.8a.7.7 0 0 1-.9-.7V6.1Z" />
      <path d="M9 4v16M15 6v16" />
    </svg>
  );
}

export function DatabaseIcon() {
  return (
    <svg viewBox="0 0 24 24" {...stroke}>
      <ellipse cx="12" cy="5.5" rx="8" ry="3" />
      <path d="M4 5.5v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6" />
      <path d="M4 11.5v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7" />
    </svg>
  );
}

export function SurveyIcon() {
  return (
    <svg viewBox="0 0 24 24" {...stroke}>
      <path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1" />
      <circle cx="12" cy="12" r="4" />
    </svg>
  );
}

export function HomeIcon() {
  return (
    <svg viewBox="0 0 24 24" {...stroke}>
      <path d="m3 10 9-7 9 7v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z" />
      <path d="M9 21v-7h6v7" />
    </svg>
  );
}

export function UserIcon() {
  return (
    <svg viewBox="0 0 24 24" {...stroke}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21c0-4 3.6-6 8-6s8 2 8 6" />
    </svg>
  );
}

export function GridIcon() {
  return (
    <svg viewBox="0 0 24 24" {...stroke}>
      <rect x="3" y="3" width="7" height="7" rx="2" />
      <rect x="14" y="3" width="7" height="7" rx="2" />
      <rect x="3" y="14" width="7" height="7" rx="2" />
      <rect x="14" y="14" width="7" height="7" rx="2" />
    </svg>
  );
}

export function DocIcon() {
  return (
    <svg viewBox="0 0 24 24" {...stroke}>
      <path d="M6 3h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
      <path d="M14 3v6h6M9 14h7M9 18h5" />
    </svg>
  );
}
