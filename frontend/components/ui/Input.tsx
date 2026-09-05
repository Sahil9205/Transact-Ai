import React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  icon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, helperText, icon, type = "text", id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs font-bold text-[#171717]"
          >
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {icon && (
            <div className="absolute left-3.5 text-[#8A8A8A] pointer-events-none flex items-center justify-center">
              {icon}
            </div>
          )}
          <input
            id={inputId}
            type={type}
            ref={ref}
            className={cn(
              "w-full bg-[#FFF9F2] border border-[#F0DED0] rounded-xl px-3.5 py-2.5 text-xs sm:text-sm text-[#171717] outline-none transition-all placeholder:text-[#8A8A8A]",
              "focus:border-[#FF203D] focus:ring-1 focus:ring-[#FF203D] focus:bg-white",
              icon && "pl-10",
              error && "border-rose-400 focus:border-rose-500 focus:ring-rose-500",
              className
            )}
            {...props}
          />
        </div>
        {helperText && !error && (
          <p className="text-[11px] text-[#5F5F5F] font-medium">{helperText}</p>
        )}
        {error && (
          <p className="text-[11px] text-rose-600 font-semibold">{error}</p>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";

export default Input;

