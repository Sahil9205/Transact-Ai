import React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", children, disabled, isLoading, ...props }, ref) => {
    const baseStyles =
      "inline-flex items-center justify-center font-bold transition-all select-none disabled:opacity-50 disabled:pointer-events-none active:scale-[0.98] cursor-pointer whitespace-nowrap";

    const variantStyles = {
      primary:
        "bg-[#FF203D] hover:bg-[#E71937] text-white shadow-sm hover:shadow",
      secondary:
        "bg-[#FFF4E6] hover:bg-[#FFE8C7] text-[#171717] border border-[#F0DED0]",
      outline:
        "bg-transparent hover:bg-[#FFF4E6] text-[#171717] border border-[#F0DED0] hover:border-[#FFD9A8]",
      ghost:
        "bg-transparent hover:bg-[#FFF4E6] text-[#5F5F5F] hover:text-[#171717]",
      danger:
        "bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200",
    };

    const sizeStyles = {
      sm: "text-xs px-3 py-1.5 rounded-lg h-8 gap-1.5",
      md: "text-xs sm:text-sm px-4 py-2.5 rounded-xl h-10 gap-2",
      lg: "text-sm sm:text-base px-6 py-3.5 rounded-2xl h-12 gap-2.5 font-extrabold shadow-md",
    };

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <>
            <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
            <span>Loading...</span>
          </>
        ) : (
          children
        )}
      </button>
    );
  }
);
Button.displayName = "Button";

export default Button;

