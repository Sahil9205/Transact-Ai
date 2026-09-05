"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  User,
  ArrowRight,
  Sparkles,
  ShieldCheck,
  Zap,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Card from "@/components/ui/Card";
import { useToast } from "@/components/ui/Toast";
import MandalaAccent from "@/components/patterns/MandalaAccent";

export default function UserLoginPage() {
  const router = useRouter();
  const { showToast } = useToast();

  const [userIdInput, setUserIdInput] = useState("buyer-1");

  const handleLogin = (id: string) => {
    localStorage.setItem("transactai_active_user_id", id);
    showToast(`Signed in as ${id}`);
    router.push("/user/dashboard");
  };

  return (
    <div className="min-h-screen bg-[#FFF9F2] flex items-center justify-center p-4 sm:p-8 relative overflow-hidden">
      <MandalaAccent className="absolute -top-24 -right-24 w-80 h-80 text-[#FF7A18] opacity-[0.25] pointer-events-none" />
      <MandalaAccent className="absolute -bottom-24 -left-24 w-80 h-80 text-[#FF203D] opacity-[0.25] pointer-events-none" />


      <div className="w-full max-w-md relative z-10 space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FFF4E6] border border-[#FFD9A8] text-xs font-bold text-[#FF7A18] uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Buyer Access</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-[#171717] tracking-tight">
            TransactAI Buyer Console
          </h1>
          <p className="text-xs sm:text-sm text-[#5F5F5F] max-w-sm mx-auto">
            Manage spending limits, review agent purchases, and audit automated settlements.
          </p>
        </div>

        <Card className="p-6 sm:p-8 bg-white border-[#F0DED0] shadow-[0_16px_40px_rgba(240,222,208,0.6)] space-y-5">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (userIdInput.trim()) handleLogin(userIdInput.trim());
            }}
            className="space-y-4"
          >
            <div>
              <label className="block text-xs font-bold text-[#171717] mb-1.5">
                Buyer User ID or Email
              </label>
              <Input
                required
                icon={<User className="w-4 h-4" />}
                placeholder="e.g. buyer-1 or user_sahil"
                value={userIdInput}
                onChange={(e) => setUserIdInput(e.target.value)}
              />
            </div>

            <Button type="submit" className="w-full text-xs font-extrabold h-11">
              <span>Enter Buyer Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </form>

          {/* Quick Demo Test Accounts */}
          <div className="pt-4 border-t border-[#F0DED0] space-y-2">
            <p className="text-[11px] font-bold text-[#8A8A8A] uppercase tracking-wider">
              Quick Test Accounts
            </p>
            <div className="grid grid-cols-2 gap-2">
              {[
                { id: "buyer-1", label: "Seed Buyer 1 (Default)" },
                { id: "buyer-2", label: "Seed Buyer 2 (Strict)" },
              ].map((acc) => (
                <button
                  key={acc.id}
                  type="button"
                  onClick={() => handleLogin(acc.id)}
                  className="p-2.5 rounded-xl bg-[#FFF9F2] hover:bg-[#FFE8C7] border border-[#F0DED0] text-left transition-all cursor-pointer group"
                >
                  <div className="text-xs font-bold text-[#171717] group-hover:text-[#FF203D]">
                    {acc.id}
                  </div>
                  <div className="text-[10px] text-[#5F5F5F] truncate">{acc.label}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="text-center pt-2">
            <span className="text-xs text-[#5F5F5F]">New to TransactAI? </span>
            <Link
              href="/user/register"
              className="text-xs font-bold text-[#FF7A18] hover:text-[#FF203D] transition-colors"
            >
              Register New Buyer &rarr;
            </Link>
          </div>
        </Card>

        <div className="text-center flex items-center justify-center gap-1.5 text-xs text-[#8A8A8A]">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Every transaction requires pre-approved spending rules</span>
        </div>
      </div>
    </div>
  );
}
