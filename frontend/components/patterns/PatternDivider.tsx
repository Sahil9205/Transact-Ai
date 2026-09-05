import React from "react";

interface PatternDividerProps {
  className?: string;
}

export const PatternDivider: React.FC<PatternDividerProps> = ({
  className = "my-12 text-[#FFD9A8]",
}) => {
  return (
    <div className={`flex items-center justify-center gap-3 w-full max-w-4xl mx-auto overflow-hidden opacity-80 ${className}`}>
      {/* Left ornamental geometric line */}
      <div className="flex-1 flex items-center gap-1.5 overflow-hidden">
        <div className="h-[1px] flex-1 bg-gradient-to-r from-transparent via-[#F0DED0] to-[#FFD9A8]" />
        <div className="w-1.5 h-1.5 rotate-45 border border-[#FF9F1C] shrink-0" />
        <div className="w-1 h-1 rounded-full bg-[#FF7A18] shrink-0" />
        <div className="w-2 h-2 rotate-45 bg-[#FFE8C7] border border-[#FFD9A8] shrink-0" />
      </div>

      {/* Center Indian craft diamond & lotus motif */}
      <div className="shrink-0 flex items-center gap-2 px-2 text-[#FF7A18]">
        <svg width="28" height="20" viewBox="0 0 28 20" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M14 2 L22 10 L14 18 L6 10 Z" stroke="currentColor" strokeWidth="1.2" fill="#FFF4E6" />
          <circle cx="14" cy="10" r="3" fill="#FF203D" />
          <path d="M14 0 Q10 6 6 6 Q10 8 14 6 Q18 8 22 6 Q18 6 14 0 Z" fill="#FF9F1C" fillOpacity="0.4" />
          <path d="M14 20 Q10 14 6 14 Q10 12 14 14 Q18 12 22 14 Q18 14 14 20 Z" fill="#FF9F1C" fillOpacity="0.4" />
        </svg>
      </div>

      {/* Right ornamental geometric line */}
      <div className="flex-1 flex items-center gap-1.5 overflow-hidden">
        <div className="w-2 h-2 rotate-45 bg-[#FFE8C7] border border-[#FFD9A8] shrink-0" />
        <div className="w-1 h-1 rounded-full bg-[#FF7A18] shrink-0" />
        <div className="w-1.5 h-1.5 rotate-45 border border-[#FF9F1C] shrink-0" />
        <div className="h-[1px] flex-1 bg-gradient-to-l from-transparent via-[#F0DED0] to-[#FFD9A8]" />
      </div>
    </div>
  );
};

export default PatternDivider;

