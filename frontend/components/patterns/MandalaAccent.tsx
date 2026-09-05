import React from "react";

interface MandalaAccentProps {
  className?: string;
  size?: number;
}

export const MandalaAccent: React.FC<MandalaAccentProps> = ({
  className = "w-64 h-64 text-[#FFD9A8]/40",
  size = 256,
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 200 200"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <circle cx="100" cy="100" r="96" stroke="currentColor" strokeWidth="1.2" strokeDasharray="3 3" />
      <circle cx="100" cy="100" r="84" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="100" cy="100" r="72" stroke="currentColor" strokeWidth="1" strokeDasharray="2 4" />
      <circle cx="100" cy="100" r="54" stroke="currentColor" strokeWidth="1.2" />
      <circle cx="100" cy="100" r="32" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="100" cy="100" r="14" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="100" cy="100" r="4" fill="currentColor" />

      {/* 8-fold radial petals */}
      <g stroke="currentColor" strokeWidth="1.2">
        {[0, 45, 90, 135, 180, 225, 270, 315].map((angle) => (
          <g key={angle} transform={`rotate(${angle} 100 100)`}>
            {/* Outer Petal */}
            <path d="M100 16 C92 36, 88 56, 100 84 C112 56, 108 36, 100 16 Z" fill="currentColor" fillOpacity="0.16" />

            {/* Inner Petal */}
            <path d="M100 46 C95 58, 93 72, 100 86 C107 72, 105 58, 100 46 Z" />
            {/* Lotus Flourish */}
            <path d="M100 24 Q95 32 88 40 Q96 42 100 48 Q104 42 112 40 Q105 32 100 24 Z" />
            {/* Accent beads */}
            <circle cx="100" cy="10" r="1.5" fill="currentColor" />
            <circle cx="100" cy="28" r="1.2" fill="currentColor" />
            <circle cx="86" cy="62" r="1" fill="currentColor" />
            <circle cx="114" cy="62" r="1" fill="currentColor" />
          </g>
        ))}
      </g>

      {/* Secondary 8-fold interleaved florets */}
      <g stroke="currentColor" strokeWidth="0.8" strokeOpacity="0.7">
        {[22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5].map((angle) => (
          <g key={angle} transform={`rotate(${angle} 100 100)`}>
            <path d="M100 34 Q90 54 100 70 Q110 54 100 34 Z" />
            <circle cx="100" cy="24" r="1" fill="currentColor" />
          </g>
        ))}
      </g>
    </svg>
  );
};

export default MandalaAccent;

