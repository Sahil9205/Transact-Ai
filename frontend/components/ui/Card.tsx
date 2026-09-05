import React from "react";
import { cn } from "@/lib/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverEffect?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, hoverEffect = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "bg-white border border-[#F0DED0] rounded-2xl sm:rounded-3xl p-5 sm:p-7 shadow-[0_2px_12px_rgba(240,222,208,0.35)] relative overflow-hidden",
          hoverEffect && "hover:border-[#FFD9A8] hover:shadow-[0_8px_24px_rgba(240,222,208,0.5)] transition-all duration-200",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Card.displayName = "Card";

export default Card;

