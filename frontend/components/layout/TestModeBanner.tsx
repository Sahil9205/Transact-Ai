"use client";

import React from "react";
import { AlertCircle } from "lucide-react";

export const TestModeBanner: React.FC = () => {
  return (
    <aside
      aria-label="Test Mode Disclosure"
      className="bg-amber-500 text-amber-950 border-b border-amber-600/30 text-[11px] font-medium py-1.5 px-4 shadow-2xs relative z-50 select-none"
    >
      <div className="max-w-7xl mx-auto flex items-center justify-center gap-2 text-center flex-wrap">
        <span className="inline-flex items-center gap-1 font-bold bg-amber-950 text-amber-300 text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded">
          <AlertCircle className="w-3 h-3 text-amber-400 shrink-0" />
          Demo Notice
        </span>
        <span className="font-semibold text-amber-950">
          Demo Application. Razorpay is operating in Test Mode. Built for the Razorpay Buildathon. Not affiliated with Razorpay.
        </span>
      </div>
    </aside>
  );
};

export default TestModeBanner;
