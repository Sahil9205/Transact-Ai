"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { Check, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ToastMessage {
  id: string;
  message: string;
  type?: "success" | "error";
}

interface ToastContextType {
  showToast: (message: string, type?: "success" | "error") => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = useCallback((message: string, type: "success" | "error" = "success") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none max-w-sm w-full px-4 sm:px-0">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              "flex items-center gap-3 px-4 py-3 rounded-2xl border text-xs font-bold shadow-xl transition-all pointer-events-auto bg-white text-[#171717] animate-in slide-in-from-bottom-2",
              t.type === "error" ? "border-rose-200" : "border-[#E8CDBB]"
            )}
          >
            <span
              className={cn(
                "w-5 h-5 rounded-full flex items-center justify-center font-bold text-xs shrink-0",
                t.type === "error"
                  ? "bg-rose-100 text-rose-600"
                  : "bg-emerald-100 text-emerald-700"
              )}
            >
              {t.type === "error" ? <X className="w-3 h-3" /> : <Check className="w-3 h-3" />}
            </span>
            <span className="flex-1">{t.message}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
};
