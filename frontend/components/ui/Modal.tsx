"use client";

import React, { useEffect } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
  size?: "sm" | "md" | "lg" | "xl";
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  className,
  size = "md",
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.body.style.overflow = "unset";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: "max-w-sm",
    md: "max-w-lg",
    lg: "max-w-2xl",
    xl: "max-w-4xl",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-[#171717]/40 backdrop-blur-xs transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div
        className={cn(
          "bg-white border border-[#F0DED0] rounded-3xl p-6 sm:p-8 w-full shadow-2xl relative z-10 animate-in fade-in zoom-in-95 duration-150 max-h-[90vh] overflow-y-auto",
          sizeClasses[size],
          className
        )}
        role="dialog"
        aria-modal="true"
      >
        <div className="flex items-start justify-between mb-5">
          <div>
            <h3 className="text-xl font-black text-[#171717] tracking-tight">{title}</h3>
            {description && (
              <p className="text-xs text-[#5F5F5F] font-medium mt-1">{description}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-xl bg-[#FFF4E6] hover:bg-[#FFE8C7] text-[#5F5F5F] hover:text-[#171717] flex items-center justify-center transition-colors cursor-pointer border border-[#F0DED0]"
            aria-label="Close modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {children}
      </div>
    </div>
  );
};

export default Modal;

