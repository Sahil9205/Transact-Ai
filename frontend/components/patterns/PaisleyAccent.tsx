import React from "react";

interface PaisleyAccentProps {
  className?: string;
  size?: number;
}

export const PaisleyAccent: React.FC<PaisleyAccentProps> = ({
  className = "w-24 h-24 text-[#FFD9A8]/45",
  size = 96,
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >

      {/* Outer flowing teardrop paisley contour */}
      <path
        d="M35 85 C15 85, 10 65, 15 45 C20 25, 38 12, 60 10 C75 9, 88 18, 86 32 C84 44, 70 48, 62 42 C56 36, 58 26, 68 24 C72 23, 76 26, 75 30 C74 34, 70 36, 68 34"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Inner concentric echo */}
      <path
        d="M35 78 C20 78, 18 64, 22 48 C26 32, 40 20, 58 18 C70 17, 80 24, 78 34"
        stroke="currentColor"
        strokeWidth="1"
        strokeDasharray="2 3"
      />
      {/* Central floret lotus within paisley belly */}
      <circle cx="36" cy="60" r="10" stroke="currentColor" strokeWidth="1" />
      <circle cx="36" cy="60" r="4" fill="currentColor" fillOpacity="0.4" />
      <path d="M36 46 Q33 53 36 60 Q39 53 36 46 Z" fill="currentColor" fillOpacity="0.2" />
      <path d="M36 74 Q33 67 36 60 Q39 67 36 74 Z" fill="currentColor" fillOpacity="0.2" />
      <path d="M22 60 Q29 57 36 60 Q29 63 22 60 Z" fill="currentColor" fillOpacity="0.2" />
      <path d="M50 60 Q43 57 36 60 Q43 63 50 60 Z" fill="currentColor" fillOpacity="0.2" />
      {/* Decorative leaf feathering */}
      <circle cx="28" cy="74" r="1.5" fill="currentColor" />
      <circle cx="44" cy="74" r="1.5" fill="currentColor" />
      <circle cx="48" cy="38" r="1.5" fill="currentColor" />
      <circle cx="54" cy="46" r="1.2" fill="currentColor" />
    </svg>
  );
};

export default PaisleyAccent;

