"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Store, UserPlus, ArrowRight, ShieldCheck, ChevronDown } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { MandalaAccent } from "@/components/patterns/MandalaAccent";
import { PatternDivider } from "@/components/patterns/PatternDivider";
import { api } from "@/lib/api";
import { Merchant } from "@/lib/types";

export default function MerchantGatewayPage() {
  const router = useRouter();
  const [merchants, setMerchants] = useState<Merchant[]>([]);
  const [selectedMerchantId, setSelectedMerchantId] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadMerchants() {
      try {
        const data = await api.listMerchants();
        setMerchants(data);
        if (data.length > 0) {
          setSelectedMerchantId(data[0].provider_id);
        }
      } catch (err) {
        console.error("Failed to load merchants:", err);
      } finally {
        setLoading(false);
      }
    }
    loadMerchants();
  }, []);

  const handleOpenConsole = () => {
    if (!selectedMerchantId) {
      alert("Please select a store from the list.");
      return;
    }
    router.push(`/merchant/dashboard/${selectedMerchantId}`);
  };

  return (
    <div className="min-h-screen bg-[#FFF9F2] py-12 sm:py-16 flex flex-col items-center justify-center relative overflow-hidden">
      <div className="w-full max-w-7xl mx-auto px-5 sm:px-8 lg:px-10 flex flex-col items-center justify-center relative">
        {/* Subtle background mandala motif */}
        <div className="absolute -left-20 top-20 opacity-30 pointer-events-none">
          <MandalaAccent size={360} className="text-[#FF9F1C]" />
        </div>


        {/* Hero Header */}
        <div className="text-center max-w-3xl mx-auto mb-12 sm:mb-14 relative z-10">
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
          
          {/* CARD 1: Existing Store Partner */}
          <Card hoverEffect className="flex flex-col justify-between p-6 sm:p-8">
            <div>
              <div className="flex items-center justify-between mb-5">
                <div className="w-12 h-12 rounded-2xl bg-[#FFF4E6] border border-[#FFD9A8] flex items-center justify-center text-[#FF7A18] shadow-2xs">
                  <Store className="w-6 h-6" />
                </div>
                <Badge variant="neutral">Existing Merchant</Badge>
              </div>

              <h2 className="text-xl font-black text-[#171717] tracking-tight">
                I am an Existing Store Partner
              </h2>
              <p className="text-xs text-[#5F5F5F] mt-2 leading-relaxed font-medium">
                Already registered on TransactAI? Select your shop below to access live incoming customer orders,
                manage real-time pricing, and review daily settlements.
              </p>

              {/* Store Selector Dropdown */}
              <div className="mt-6 space-y-2">
                <label className="block text-[11px] font-bold uppercase tracking-wider text-[#171717]">
                  Select Your Store:
                </label>
                <div className="relative">
                  <select
                    id="existingStoreSelect"
                    value={selectedMerchantId}
                    onChange={(e) => setSelectedMerchantId(e.target.value)}
                    disabled={loading || merchants.length === 0}
                    className="w-full appearance-none bg-[#FFF9F2] hover:bg-[#FFF4E6] text-[#171717] font-bold text-xs rounded-xl pl-3.5 pr-10 py-3.5 border border-[#F0DED0] outline-none focus:border-[#FF203D] focus:ring-1 focus:ring-[#FF203D] cursor-pointer transition-all disabled:opacity-50"
                  >
                    {loading ? (
                      <option>Loading registered stores...</option>
                    ) : merchants.length === 0 ? (
                      <option value="">No registered stores yet</option>
                    ) : (
                      merchants.map((m) => (
                        <option key={m.provider_id} value={m.provider_id}>
                          {m.name} ({m.location || "Delhi NCR"})
                        </option>
                      ))
                    )}
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3.5 text-[#5F5F5F]">
                    <ChevronDown className="w-4 h-4" />
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-6 mt-6 border-t border-[#F0DED0]">
              <Button
                variant="primary"
                size="lg"
                onClick={handleOpenConsole}
                disabled={!selectedMerchantId}
                className="w-full bg-[#171717] hover:bg-[#FF203D] text-white font-extrabold text-xs flex items-center justify-center gap-2"
              >
                <span>Open Store Operations Console</span>
                <ArrowRight className="w-4 h-4" />
              </Button>
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
