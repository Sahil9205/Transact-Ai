import React from "react";
import Link from "next/link";
import { MandalaAccent } from "@/components/patterns/MandalaAccent";

export const Footer: React.FC = () => {
  return (
    <footer className="relative bg-[#FFF4E6] border-t border-[#F0DED0] pt-16 pb-12 overflow-hidden">
      {/* Subtle corner mandala accent */}
      <div className="absolute right-0 bottom-0 translate-x-1/3 translate-y-1/3 opacity-35 pointer-events-none">
        <MandalaAccent size={420} className="text-[#FF9F1C]" />
      </div>


      <div className="max-w-7xl mx-auto px-5 sm:px-8 lg:px-10 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-10 lg:gap-12 pb-12 border-b border-[#F0DED0]">
          
          {/* Brand Col */}
          <div className="md:col-span-2 space-y-4">
            <Link href="/" className="flex items-center gap-3 group">
              <img
                src="/logo_icon.png"
                alt="TransactAI Logo"
                className="w-10 h-10 rounded-2xl shadow-xs object-contain"
              />
              <span className="text-2xl font-black tracking-tight text-[#171717]">
                Transact<span className="text-[#FF203D]">AI</span>
              </span>
            </Link>
            <p className="text-xs text-[#5F5F5F] leading-relaxed max-w-sm font-medium">
              Provider-independent AI Commerce Execution Agent. Bridging autonomous AI assistants
              with deterministic checkout, real-time inventory verification, and automated settlements.
            </p>
            <div className="pt-2">
              <span className="inline-flex items-center gap-2 text-xs font-bold text-[#5F5F5F] bg-[#FFF9F2] px-3.5 py-1.5 rounded-full border border-[#F0DED0]">
                <span>⚡</span>
                <span>Deterministic Execution Safeguards Active</span>
              </span>
            </div>
          </div>

          {/* Col 1: Solutions */}
          <div className="space-y-3">
            <div className="text-xs font-black uppercase tracking-wider text-[#171717]">Solutions</div>
            <ul className="space-y-2 text-xs font-medium text-[#5F5F5F]">
              <li><Link href="/user/dashboard" className="hover:text-[#FF203D] transition-colors">Users &amp; Buyers</Link></li>
              <li><Link href="/merchant" className="hover:text-[#FF203D] transition-colors">Local Merchants</Link></li>
              <li><Link href="/merchant/register" className="hover:text-[#FF203D] transition-colors">Merchant Onboarding</Link></li>
              <li><Link href="/enterprise" className="hover:text-[#FF203D] transition-colors">Enterprise Platforms</Link></li>
            </ul>
          </div>

          {/* Col 2: Developers */}
          <div className="space-y-3">
            <div className="text-xs font-black uppercase tracking-wider text-[#171717]">Developers</div>
            <ul className="space-y-2 text-xs font-medium text-[#5F5F5F]">
              <li><Link href="/developer" className="hover:text-[#FF203D] transition-colors">Developer Portal</Link></li>
              <li><Link href="/developer#mcp" className="hover:text-[#FF203D] transition-colors">Claude MCP Tools</Link></li>
              <li><Link href="/developer#chatgpt" className="hover:text-[#FF203D] transition-colors">ChatGPT Plugin API</Link></li>
              <li><Link href="/developer#gemini" className="hover:text-[#FF203D] transition-colors">Gemini Extensions</Link></li>
            </ul>
          </div>

          {/* Col 3: Integrations & Trust */}
          <div className="space-y-3">
            <div className="text-xs font-black uppercase tracking-wider text-[#171717]">Trust &amp; Payouts</div>
            <ul className="space-y-2 text-xs font-medium text-[#5F5F5F]">
              <li><Link href="/#trust" className="hover:text-[#FF203D] transition-colors">Execution Pipeline</Link></li>
              <li><Link href="/#recovery" className="hover:text-[#FF203D] transition-colors">Failure Recovery</Link></li>
              <li><span className="text-[#5F5F5F]">256-bit Encrypted</span></li>
              <li><Link href="/enterprise" className="hover:text-[#FF203D] transition-colors">Talk to TransactAI</Link></li>
            </ul>
          </div>

        </div>

        {/* Subordinate Footer Bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-medium text-[#5F5F5F]">
          <div>
            &copy; {new Date().getFullYear()} TransactAI Platform Inc. All rights reserved.
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold text-[#8A8A8A] tracking-wider uppercase">Infrastructure:</span>
            <span className="font-bold text-[#171717] bg-white px-3 py-1 rounded-full border border-[#F0DED0] shadow-2xs">
              Powered by Razorpay
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};
