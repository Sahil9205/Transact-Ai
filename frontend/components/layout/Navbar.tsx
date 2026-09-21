"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Menu, X, ArrowUpRight, Github } from "lucide-react";
import { Button } from "@/components/ui/Button";

export const Navbar: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { label: "Developers", href: "/developer" },
    { label: "Architecture", href: "/developer/architecture" },
    { label: "Merchants", href: "/merchant" },
    { label: "Buyer Guardrails", href: "/user/dashboard" },
    { label: "Enterprise", href: "/enterprise", badge: "Concept" },
  ];

  return (
    <header className="bg-white/95 backdrop-blur-md border-b border-[#F0DED0] sticky top-0 z-40 shadow-[0_2px_12px_rgba(240,222,208,0.4)]">
      <div className="w-full max-w-7xl mx-auto px-5 sm:px-8 lg:px-10 min-h-[82px] py-4 flex items-center justify-between gap-4">
        
        {/* Brand Logo Lockup */}
        <Link href="/" className="flex items-center gap-3.5 group shrink-0">
          <img
            src="/logo_icon.png"
            alt="TransactAI Logo"
            className="w-11 h-11 rounded-2xl shadow-xs group-hover:scale-105 transition-transform object-contain"
          />
          <div>
            <span className="text-2xl font-black tracking-tight text-[#171717]">
              Transact<span className="text-[#FF203D]">AI</span>
            </span>
          </div>
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="hidden lg:flex items-center gap-6 text-xs font-bold text-[#5F5F5F]">
          {navLinks.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="hover:text-[#171717] transition-colors flex items-center gap-1.5"
            >
              <span>{link.label}</span>
              {link.badge && (
                <span className="text-[10px] font-mono font-semibold uppercase px-1.5 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-300">
                  {link.badge}
                </span>
              )}
            </Link>
          ))}
        </nav>

        {/* Action Controls */}
        <div className="hidden sm:flex items-center gap-2.5">
          <a
            href="https://github.com/Sahil9205/Transact-Ai"
            target="_blank"
            rel="noreferrer"
            className="text-xs font-bold text-[#5F5F5F] hover:text-[#171717] flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-[#F0DED0] bg-[#FFF9F2] hover:bg-[#FFF4E6] transition-colors"
          >
            <Github className="w-3.5 h-3.5" />
            <span>GitHub</span>
          </a>
          <Link href="/user/login">
            <Button variant="ghost" size="sm" className="font-bold">
              Sign In
            </Button>
          </Link>
          <Link href="/merchant">
            <Button variant="secondary" size="sm" className="font-bold">
              Merchant Portal
            </Button>
          </Link>
          <Link href="/merchant/register">
            <Button variant="primary" size="sm" className="font-extrabold shadow-sm">
              Get Started &rarr;
            </Button>
          </Link>
        </div>

        {/* Mobile Hamburger Toggle */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="lg:hidden w-10 h-10 rounded-xl bg-[#FFF4E6] border border-[#F0DED0] flex items-center justify-center text-[#171717] cursor-pointer"
          aria-label="Toggle navigation menu"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-white border-b border-[#F0DED0] px-6 py-6 space-y-4 animate-in slide-in-from-top-2">
          <div className="flex flex-col space-y-3 text-sm font-bold text-[#171717]">
            {navLinks.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className="py-1 hover:text-[#FF203D] flex items-center justify-between"
              >
                <span>{link.label}</span>
                {link.badge && (
                  <span className="text-[10px] font-mono font-semibold uppercase px-1.5 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-300">
                    {link.badge}
                  </span>
                )}
              </Link>
            ))}
          </div>
          <div className="pt-4 border-t border-[#F0DED0] flex flex-col gap-2.5">
            <a
              href="https://github.com/Sahil9205/Transact-Ai"
              target="_blank"
              rel="noreferrer"
              className="flex items-center justify-center gap-2 p-2.5 rounded-xl border border-[#F0DED0] text-xs font-bold text-[#171717]"
            >
              <Github className="w-4 h-4" />
              <span>View on GitHub</span>
            </a>
            <Link href="/user/login" onClick={() => setMobileMenuOpen(false)}>
              <Button variant="secondary" size="md" className="w-full">
                Sign In as Buyer
              </Button>
            </Link>
            <Link href="/merchant/register" onClick={() => setMobileMenuOpen(false)}>
              <Button variant="primary" size="md" className="w-full font-black">
                Register Store &rarr;
              </Button>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};
