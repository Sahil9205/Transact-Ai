import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "brand" | "success" | "warning" | "neutral" | "danger" | "outline";
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = "brand",
  children,
  ...props
}) => {
  const variantStyles = {
    brand: "bg-[#FFF4E6] text-[#FF7A18] border-[#FFD9A8]",
    success: "bg-emerald-50 text-emerald-700 border-emerald-200",
    warning: "bg-amber-50 text-amber-700 border-amber-200",
    neutral: "bg-[#FFF9F2] text-[#5F5F5F] border-[#F0DED0]",
    danger: "bg-rose-50 text-rose-700 border-rose-200",
    outline: "bg-transparent text-[#5F5F5F] border-[#F0DED0]",
  };


  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold border tracking-wide select-none",
        variantStyles[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};

export default Badge;

