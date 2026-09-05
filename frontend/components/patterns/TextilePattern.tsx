import React from "react";

interface TextilePatternProps {
  className?: string;
  opacity?: number;
}

export const TextilePattern: React.FC<TextilePatternProps> = ({
  className = "absolute inset-0 pointer-events-none",
  opacity = 0.23,
}) => {

  return (
    <div
      className={className}
      style={{
        opacity,
        backgroundImage: `radial-gradient(#FF9F1C 0.75px, transparent 0.75px), radial-gradient(#FF203D 0.75px, #FFF9F2 0.75px)`,
        backgroundSize: "30px 30px",
        backgroundPosition: "0 0, 15px 15px",
      }}
      aria-hidden="true"
    />
  );
};

export default TextilePattern;

