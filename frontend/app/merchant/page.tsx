"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Store,
  UserPlus,
  ArrowRight,
  ShieldCheck,
  Mail,
  Lock,
  Eye,
  EyeOff,
  KeyRound,
  AlertCircle,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { MandalaAccent } from "@/components/patterns/MandalaAccent";
import { PatternDivider } from "@/components/patterns/PatternDivider";
import { api } from "@/lib/api";

export default function MerchantGatewayPage() {
  const router = useRouter();

  // Authentication State
  const [loginId, setLoginId] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [timeLeft, setTimeLeft] = useState(0);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // 5-second auto-mask timer for password visibility
  const togglePasswordVisibility = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (intervalRef.current) clearInterval(intervalRef.current);

    if (!showPassword) {
      setShowPassword(true);
      setTimeLeft(5);

      intervalRef.current = setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 1) {
            if (intervalRef.current) clearInterval(intervalRef.current);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      timerRef.current = setTimeout(() => {
        setShowPassword(false);
        setTimeLeft(0);
      }, 5000);
    } else {
      setShowPassword(false);
      setTimeLeft(0);
    }
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");

    if (!loginId.trim() || !password) {
      setErrorMessage("Please enter both Login ID and password.");
      return;
    }

    try {
      setLoading(true);
      const res = await api.loginMerchant({
        login_id: loginId.trim(),
        password,
      });

      localStorage.setItem("transact_merchant_token", res.access_token);
      localStorage.setItem("transact_merchant_user", JSON.stringify(res.merchant));

      const targetId = res.merchant.merchant_id || res.merchant.provider_id;
      router.push(`/merchant/dashboard/${targetId}`);
    } catch (err: any) {
      setErrorMessage(
        err.message || "Invalid credentials. Please verify your Login ID and password."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = (id: string, pass: string = "Merchant@2026") => {
    setLoginId(id);
    setPassword(pass);
    setErrorMessage("");
  };

  return (
    <div className="min-h-screen bg-[#FFF9F2] py-12 sm:py-16 flex flex-col items-center justify-center relative overflow-hidden">
      <div className="w-full max-w-7xl mx-auto px-5 sm:px-8 lg:px-10 flex flex-col items-center justify-center relative">
        {/* Subtle background mandala motif */}
        <div className="absolute -left-20 top-20 opacity-30 pointer-events-none">
          <MandalaAccent size={360} className="text-[#FF9F1C]" />
        </div>

        {/* Hero Header */}
        <div className="text-center max-w-3xl mx-auto mb-10 sm:mb-12 relative z-10">
          <Badge variant="brand" className="mb-4">
            Commerce Operations Gateway
          </Badge>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-[#171717] tracking-tight leading-[1.15]">
            Merchant Operations &amp; Partner Hub
          </h1>
          <p className="mt-4 text-[#5F5F5F] text-sm sm:text-base leading-relaxed max-w-2xl mx-auto font-medium">
            Empowering local stores, restaurants, and confectioneries to fulfill instant programmatic purchases
            from frontier AI assistants with automated Razorpay payouts.
          </p>
        </div>

        {/* The 2 Core Gateway Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8 w-full max-w-4xl relative z-10">
          
          {/* CARD 1: Existing Store Partner - Secure Login */}
          <Card hoverEffect className="flex flex-col justify-between p-6 sm:p-8">
            <div>
              <div className="flex items-center justify-between mb-5">
                <div className="w-12 h-12 rounded-2xl bg-[#FFF4E6] border border-[#FFD9A8] flex items-center justify-center text-[#FF7A18] shadow-2xs">
                  <Store className="w-6 h-6" />
                </div>
                <Badge variant="neutral">Existing Merchant</Badge>
              </div>

              <h2 className="text-xl font-black text-[#171717] tracking-tight">
                Sign In to Store Console
              </h2>
              <p className="text-xs text-[#5F5F5F] mt-2 leading-relaxed font-medium">
                Enter your vendor credentials to access live incoming customer orders, manage real-time pricing,
                and update instant stock availability.
              </p>

              {/* Error Banner */}
              {errorMessage && (
                <div className="mt-4 p-3 rounded-xl bg-rose-50 border border-rose-200 flex items-center gap-2.5 text-xs text-rose-700 font-semibold">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}

              {/* Login Form */}
              <form onSubmit={handleLogin} className="mt-5 space-y-4">
                {/* Login ID Input */}
                <div>
                  <label className="block text-[11px] font-bold uppercase tracking-wider text-[#171717] mb-1.5">
                    User ID (Email, Phone, or Store Name)
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={loginId}
                      onChange={(e) => setLoginId(e.target.value)}
                      placeholder="e.g. zepto@quickcommerce.com or Sharma Sweets"
                      required
                      className="w-full bg-[#FFF9F2] focus:bg-white text-[#171717] font-semibold text-xs rounded-xl pl-9 pr-3.5 py-3 border border-[#F0DED0] outline-none focus:border-[#FF203D] focus:ring-1 focus:ring-[#FF203D] transition-all"
                    />
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#8A8A8A]">
                      <Mail className="w-4 h-4" />
                    </div>
                  </div>
                </div>

                {/* Password Input with 5-Second Eye Toggle */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="block text-[11px] font-bold uppercase tracking-wider text-[#171717]">
                      Password
                    </label>
                    {showPassword && timeLeft > 0 && (
                      <span className="text-[10px] font-mono font-bold text-[#FF7A18] bg-[#FFF4E6] px-2 py-0.5 rounded-full animate-pulse border border-[#FFD9A8]">
                        Auto-hides in {timeLeft}s
                      </span>
                    )}
                  </div>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter store password"
                      required
                      className="w-full bg-[#FFF9F2] focus:bg-white text-[#171717] font-semibold text-xs rounded-xl pl-9 pr-11 py-3 border border-[#F0DED0] outline-none focus:border-[#FF203D] focus:ring-1 focus:ring-[#FF203D] transition-all font-mono"
                    />
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#8A8A8A]">
                      <Lock className="w-4 h-4" />
                    </div>
                    {/* Eye toggle button */}
                    <button
                      type="button"
                      onClick={togglePasswordVisibility}
                      className="absolute inset-y-0 right-0 flex items-center pr-3 text-[#8A8A8A] hover:text-[#171717] cursor-pointer transition-colors"
                      title={showPassword ? "Hide password" : "Show password (auto-hides after 5s)"}
                      aria-label="Toggle password visibility"
                    >
                      {showPassword ? (
                        <EyeOff className="w-4 h-4 text-[#FF7A18]" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Submit Button */}
                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  disabled={loading}
                  className="w-full bg-[#171717] hover:bg-[#FF203D] text-white font-extrabold text-xs flex items-center justify-center gap-2 mt-2"
                >
                  <span>{loading ? "Authenticating Store..." : "Access Store Operations Console"}</span>
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </form>

              {/* Quick Evaluator Test Logins */}
              <div className="mt-5 pt-4 border-t border-[#F0DED0]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-bold text-[#737373] uppercase tracking-wider">
                    ⚡ Evaluator Quick Test Logins:
                  </span>
                  <span className="text-[10px] font-mono text-[#FF7A18] font-bold">
                    PW: Merchant@2026
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => handleDemoLogin("zepto@quickcommerce.com")}
                    className="text-left px-2.5 py-1.5 bg-[#FFF4E6] hover:bg-[#FFE8C7] rounded-xl border border-[#FFD9A8] text-[11px] font-bold text-[#171717] transition-all flex items-center justify-between cursor-pointer"
                  >
                    <span>⚡ Zepto Hub</span>
                    <KeyRound className="w-3 h-3 text-[#FF7A18]" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDemoLogin("contact@sharmasweets.in")}
                    className="text-left px-2.5 py-1.5 bg-[#FFF4E6] hover:bg-[#FFE8C7] rounded-xl border border-[#FFD9A8] text-[11px] font-bold text-[#171717] transition-all flex items-center justify-between cursor-pointer"
                  >
                    <span>🍬 Sharma Sweets</span>
                    <KeyRound className="w-3 h-3 text-[#FF7A18]" />
                  </button>
                </div>
              </div>
            </div>

            <div className="pt-4 mt-4 border-t border-[#F0DED0] flex items-center justify-between text-[11px] text-[#737373]">
              <span className="inline-flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                <span>PBKDF2 &amp; RFC 7519 JWT Scoped</span>
              </span>
              <Link href="/merchant/login" className="font-bold text-[#FF7A18] hover:underline">
                Portal Login &rarr;
              </Link>
            </div>
          </Card>

          {/* CARD 2: New Store Partner Registration */}
          <Card hoverEffect className="flex flex-col justify-between p-6 sm:p-8">
            <div>
              <div className="flex items-center justify-between mb-5">
                <div className="w-12 h-12 rounded-2xl bg-[#FFE8C7] border border-[#FFD9A8] flex items-center justify-center text-[#FF203D] shadow-2xs">
                  <UserPlus className="w-6 h-6" />
                </div>
                <Badge variant="success">New Merchant</Badge>
              </div>

              <h2 className="text-xl font-black text-[#171717] tracking-tight">
                I am a New Store Partner
              </h2>
              <p className="text-xs text-[#5F5F5F] mt-2 leading-relaxed font-medium">
                Register your shop or restaurant in 2 minutes via our 6-step guided onboarding wizard. Begin fulfilling
                programmatic purchases from AI users across India.
              </p>

              <div className="mt-6 space-y-2.5 text-xs text-[#171717] font-medium">
                <div className="flex items-center gap-2.5">
                  <span className="w-4 h-4 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-[10px] shrink-0">✓</span>
                  <span>100% upfront prepaid customer orders</span>
                </div>
                <div className="flex items-center gap-2.5">
                  <span className="w-4 h-4 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-[10px] shrink-0">✓</span>
                  <span>Flexible pricing by piece, kg, or volume</span>
                </div>
                <div className="flex items-center gap-2.5">
                  <span className="w-4 h-4 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-[10px] shrink-0">✓</span>
                  <span>Automatic menu synchronization with AI assistants</span>
                </div>
              </div>
            </div>

            <div className="pt-6 mt-6 border-t border-[#F0DED0]">
              <Link href="/merchant/register" className="w-full block">
                <Button variant="primary" size="lg" className="w-full font-extrabold text-xs flex items-center justify-center gap-2">
                  <span>Start 6-Step Onboarding Wizard</span>
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            </div>
          </Card>

        </div>

        <PatternDivider className="my-12" />

        {/* Supported AI Ecosystem Strip */}
        <div className="w-full max-w-4xl text-center">
          <div className="text-[11px] font-bold uppercase tracking-wider text-[#5F5F5F] mb-4">
            Integrated Across Frontier Autonomous Agents &amp; Payment Networks
          </div>
          <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-6 text-xs font-bold text-[#171717] font-mono">
            <div className="flex items-center gap-2 bg-[#FFF4E6] px-3.5 py-2 rounded-xl border border-[#F0DED0]">
              <span className="w-2 h-2 rounded-full bg-[#FF7A18]" />
              <span>Claude (MCP Tools)</span>
            </div>
            <div className="flex items-center gap-2 bg-[#FFF4E6] px-3.5 py-2 rounded-xl border border-[#F0DED0]">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span>ChatGPT (Actions)</span>
            </div>
            <div className="flex items-center gap-2 bg-[#FFF4E6] px-3.5 py-2 rounded-xl border border-[#F0DED0]">
              <span className="w-2 h-2 rounded-full bg-[#FF9F1C]" />
              <span>Gemini Extensions</span>
            </div>
            <div className="flex items-center gap-2 bg-[#FFF4E6] px-3.5 py-2 rounded-xl border border-[#F0DED0]">
              <span className="w-2 h-2 rounded-full bg-[#FF203D]" />
              <span>Razorpay Instant Payouts</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
