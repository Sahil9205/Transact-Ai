"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Sparkles,
  ShieldCheck,
  Store,
  UserCheck,
  Code,
  Building2,
  ArrowRight,
  Zap,
  CheckCircle2,
  Lock,
  Search,
  Truck,
  TrendingUp,
  Cpu,
  Layers,
  ChevronRight,
  ShieldAlert,
  ShoppingBag,
  ExternalLink,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import MandalaAccent from "@/components/patterns/MandalaAccent";
import PaisleyAccent from "@/components/patterns/PaisleyAccent";
import PatternDivider from "@/components/patterns/PatternDivider";
import TextilePattern from "@/components/patterns/TextilePattern";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<"merchants" | "buyers" | "developers" | "enterprises">(
    "merchants"
  );

  return (
    <div className="min-h-screen bg-[#FFF9F2] text-[#171717] overflow-hidden">
      {/* 1. HERO & WHAT: The Agentic Commerce Layer */}
      <section className="relative pt-20 pb-20 sm:pt-28 sm:pb-28 overflow-hidden bg-gradient-to-b from-[#FFF4E6]/70 via-[#FFF9F2] to-[#FFF9F2]">
        {/* Visible Indian Craft Vector Watermarks & Texture */}
        <TextilePattern className="absolute inset-0 pointer-events-none" opacity={0.20} />
        <MandalaAccent className="absolute -top-28 -right-28 w-[460px] h-[460px] text-[#FF7A18] opacity-[0.25] pointer-events-none" />
        <PaisleyAccent className="absolute -bottom-20 -left-20 w-80 h-80 text-[#FF203D] opacity-[0.24] pointer-events-none rotate-45" />


        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          {/* Trust Pill */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#FFE8C7]/70 border border-[#FFD9A8] text-xs font-bold text-[#FF7A18] uppercase tracking-wider mb-6 shadow-2xs">
            <Sparkles className="w-3.5 h-3.5 text-[#FF203D]" />
            <span>The Agentic Commerce Layer • Powered by Razorpay</span>
          </div>

          {/* Master Headline */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight text-[#171717] max-w-5xl mx-auto leading-[1.1]">
            Where AI Agents Safely Discover, Buy, and{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FF7A18] via-[#FF203D] to-[#E71937]">
              Transact in the Real World
            </span>
          </h1>

          {/* Subtitle */}
          <p className="mt-6 text-base sm:text-lg text-[#5F5F5F] max-w-3xl mx-auto leading-relaxed font-medium">
            LLMs can converse, but they cannot safely transact. TransactAI provides the missing bridge:
            <strong className="text-[#171717] font-bold"> deterministic spending guardrails</strong>,
            <strong className="text-[#171717] font-bold"> semantic vector catalog discovery</strong>, and
            <strong className="text-[#171717] font-bold"> instant automated Razorpay settlements</strong> for local merchants and buyers.
          </p>

          {/* Primary Action Cluster */}
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link href="/merchant">
              <Button size="lg" className="text-xs sm:text-sm font-extrabold h-12 px-6 shadow-[0_4px_16px_rgba(255,32,61,0.25)]">
                <Store className="w-4 h-4 mr-2" />
                <span>Launch Merchant Console</span>
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>

            <Link href="/user/onboarding">
              <Button size="lg" variant="outline" className="text-xs sm:text-sm font-bold h-12 px-6">
                <ShieldAlert className="w-4 h-4 mr-2 text-[#FF7A18]" />
                <span>Configure Buyer Guardrails</span>
              </Button>
            </Link>

            <Link href="/developer">
              <Button size="lg" variant="ghost" className="text-xs sm:text-sm font-bold h-12 px-5 text-[#5F5F5F] hover:text-[#171717]">
                <Code className="w-4 h-4 mr-1.5" />
                <span>MCP Docs</span>
              </Button>
            </Link>
          </div>

          {/* Subordinate Trust Proof */}
          <div className="mt-14 pt-8 border-t border-[#F0DED0]/80 max-w-4xl mx-auto flex flex-wrap items-center justify-center gap-8 text-xs font-semibold text-[#8A8A8A]">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Zero Rogue Spending Guarantee</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>100% Real-Time Stock Parity</span>
            </div>
            <div className="flex items-center gap-2">
              <Lock className="w-4 h-4 text-emerald-600" />
              <span>Razorpay 256-bit Encrypted Settlement</span>
            </div>
          </div>
        </div>
      </section>

      <PatternDivider className="max-w-4xl mx-auto my-6" />

      {/* 2. WHY: The Problem with LLMs in Commerce */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto space-y-3 mb-14">
          <Badge variant="outline" className="text-[11px] font-bold uppercase tracking-wider text-[#FF7A18] border-[#FFD9A8] bg-[#FFF4E6]">
            The Autonomous Commerce Gap
          </Badge>
          <h2 className="text-3xl sm:text-4xl font-black text-[#171717] tracking-tight">
            Why AI Agents Cannot Transact Without TransactAI
          </h2>
          <p className="text-xs sm:text-sm text-[#5F5F5F]">
            LLMs are probabilistic prediction engines. Financial transactions require mathematical certainty.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* The Danger: Unchecked LLMs */}
          <div className="bg-white rounded-3xl p-8 border border-rose-200/80 shadow-sm space-y-5 relative overflow-hidden">
            <div className="w-12 h-12 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold text-lg">
              ✕
            </div>
            <h3 className="text-xl font-black text-rose-950">
              Unconstrained Agentic Checkout
            </h3>
            <ul className="space-y-3 text-xs text-[#5F5F5F] leading-relaxed">
              <li className="flex items-start gap-2.5">
                <span className="font-bold text-rose-500 shrink-0">&bull;</span>
                <span><strong className="text-[#171717]">Hallucinated Products:</strong> The agent suggests and orders items no merchant actually has in physical stock.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <span className="font-bold text-rose-500 shrink-0">&bull;</span>
                <span><strong className="text-[#171717]">Rogue Spending Sprees:</strong> A loop error or manipulated prompt drains the user&apos;s linked account without hard spending limits.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <span className="font-bold text-rose-500 shrink-0">&bull;</span>
                <span><strong className="text-[#171717]">Failed Fulfillment:</strong> Unverified pricing units (e.g. charging ₹200 for 100g instead of 1kg) causing merchant rejection.</span>
              </li>
            </ul>
          </div>

          {/* The TransactAI Solution */}
          <div className="bg-white rounded-3xl p-8 border border-emerald-200/80 shadow-sm space-y-5 relative overflow-hidden">
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold text-lg">
              ✓
            </div>
            <h3 className="text-xl font-black text-emerald-950">
              The TransactAI Deterministic Guarantee
            </h3>
            <ul className="space-y-3 text-xs text-[#5F5F5F] leading-relaxed">
              <li className="flex items-start gap-2.5">
                <span className="font-bold text-emerald-600 shrink-0">&bull;</span>
                <span><strong className="text-[#171717]">Mathematical Policy Engine:</strong> Hard daily limit and per-transaction bounds enforced at database level before link generation.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <span className="font-bold text-emerald-600 shrink-0">&bull;</span>
                <span><strong className="text-[#171717]">Live Qdrant Vector Catalogs:</strong> Embeddings match user desires exclusively to items validated as in-stock by local stores.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <span className="font-bold text-emerald-600 shrink-0">&bull;</span>
                <span><strong className="text-[#171717]">Automated Razorpay Payouts:</strong> 100% compliant settlements straight to verified merchant bank accounts with webhook idempotency.</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      <PatternDivider className="max-w-4xl mx-auto my-6" />

      {/* 3. WHOM: 4 Core Stakeholders Interactive Showcase */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto space-y-3 mb-10">
          <Badge variant="outline" className="text-[11px] font-bold uppercase tracking-wider text-[#FF7A18] border-[#FFD9A8] bg-[#FFF4E6]">
            Ecosystem Stakeholders
          </Badge>
          <h2 className="text-3xl sm:text-4xl font-black text-[#171717] tracking-tight">
            Engineered for Every Surface of Agentic Commerce
          </h2>
        </div>

        {/* Tab Selector */}
        <div className="flex justify-center mb-8">
          <div className="inline-flex p-1.5 bg-[#FFF4E6] border border-[#F0DED0] rounded-2xl gap-1 text-xs font-bold">
            {[
              { id: "merchants", label: "For Merchants", icon: <Store className="w-3.5 h-3.5" /> },
              { id: "buyers", label: "For Buyers", icon: <UserCheck className="w-3.5 h-3.5" /> },
              { id: "developers", label: "For Developers", icon: <Code className="w-3.5 h-3.5" /> },
              { id: "enterprises", label: "For Enterprises", icon: <Building2 className="w-3.5 h-3.5" /> },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl transition-all cursor-pointer ${
                  activeTab === tab.id
                    ? "bg-[#FF203D] text-white shadow-xs"
                    : "text-[#5F5F5F] hover:text-[#171717]"
                }`}
              >
                {tab.icon}
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content Cards */}
        <div className="bg-white rounded-3xl p-8 sm:p-12 border border-[#F0DED0] shadow-sm relative overflow-hidden">
          {activeTab === "merchants" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-6 space-y-4">
                <Badge variant="outline" className="text-[10px] text-[#FF7A18] border-[#FFD9A8] bg-[#FFF4E6]">
                  Storefront Operations
                </Badge>
                <h3 className="text-2xl sm:text-3xl font-black text-[#171717] tracking-tight">
                  Turn Your Local Storefront into an AI-Ready Merchant Hub
                </h3>
                <p className="text-xs sm:text-sm text-[#5F5F5F] leading-relaxed">
                  Join the agentic economy in under 3 minutes. Configure weight-based groceries (₹/kg) or unit goods, toggle store state, and receive live incoming orders directly dispatched by autonomous AI shoppers.
                </p>
                <div className="pt-2">
                  <Link href="/merchant/register">
                    <Button className="text-xs font-extrabold">
                      <span>Begin 6-Step Guided Onboarding</span>
                      <ArrowRight className="w-4 h-4 ml-1" />
                    </Button>
                  </Link>
                </div>
              </div>
              <div className="lg:col-span-6 bg-[#FFF9F2] border border-[#F0DED0] rounded-2xl p-6 space-y-3">
                <div className="text-xs font-bold text-[#171717] flex items-center justify-between">
                  <span>Merchant Highlights</span>
                  <span className="text-emerald-700 font-mono text-[10px] bg-emerald-50 px-2 py-0.5 rounded-md font-bold">Live</span>
                </div>
                <div className="space-y-2 text-xs text-[#5F5F5F]">
                  <div className="p-3 bg-white rounded-xl border border-[#F0DED0] flex items-center justify-between">
                    <span>Flexible Pricing Models</span>
                    <strong className="text-[#171717]">Fixed Unit • ₹/kg • Volume</strong>
                  </div>
                  <div className="p-3 bg-white rounded-xl border border-[#F0DED0] flex items-center justify-between">
                    <span>One-Click Stock Toggles</span>
                    <strong className="text-emerald-700">● In Stock ↔ ○ Out of Stock</strong>
                  </div>
                  <div className="p-3 bg-white rounded-xl border border-[#F0DED0] flex items-center justify-between">
                    <span>Bank Payouts</span>
                    <strong className="text-[#171717]">Automated Razorpay Settlements</strong>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "buyers" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-6 space-y-4">
                <Badge variant="outline" className="text-[10px] text-[#FF7A18] border-[#FFD9A8] bg-[#FFF4E6]">
                  Buyer Protection
                </Badge>
                <h3 className="text-2xl sm:text-3xl font-black text-[#171717] tracking-tight">
                  Unleash AI Convenience with Hard Mathematical Spending Limits
                </h3>
                <p className="text-xs sm:text-sm text-[#5F5F5F] leading-relaxed">
                  Never worry about unauthorized charges. Set custom per-transaction ceilings, daily cumulative spending caps, and category whitelisting. AI agents can only transact what you pre-approve.
                </p>
                <div className="pt-2">
                  <Link href="/user/onboarding">
                    <Button className="text-xs font-extrabold">
                      <span>Set Spending Guardrails &rarr;</span>
                    </Button>
                  </Link>
                </div>
              </div>
              <div className="lg:col-span-6 bg-[#FFF9F2] border border-[#F0DED0] rounded-2xl p-6 space-y-3">
                <div className="text-xs font-bold text-[#171717]">Active Guardrail Simulation</div>
                <div className="p-4 bg-white rounded-xl border border-[#F0DED0] space-y-2">
                  <div className="flex justify-between text-xs font-bold">
                    <span>Daily Spending Cap</span>
                    <span className="font-mono text-[#FF203D]">₹3,000 / day</span>
                  </div>
                  <div className="w-full h-2 bg-[#FFF4E6] rounded-full overflow-hidden">
                    <div className="w-1/3 h-full bg-[#FF7A18] rounded-full" />
                  </div>
                  <div className="text-[11px] text-[#5F5F5F] flex justify-between">
                    <span>Spent Today: ₹1,000</span>
                    <span>Remaining: ₹2,000</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "developers" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-6 space-y-4">
                <Badge variant="outline" className="text-[10px] text-[#FF7A18] border-[#FFD9A8] bg-[#FFF4E6]">
                  Developer First
                </Badge>
                <h3 className="text-2xl sm:text-3xl font-black text-[#171717] tracking-tight">
                  Drop-In MCP Tools for Claude, ChatGPT &amp; Gemini
                </h3>
                <p className="text-xs sm:text-sm text-[#5F5F5F] leading-relaxed">
                  Implement autonomous commerce in minutes. Register standard Model Context Protocol (MCP) tools for semantic product search, policy validation, and payment order generation.
                </p>
                <div className="pt-2">
                  <Link href="/developer">
                    <Button className="text-xs font-extrabold">
                      <span>Explore Developer Specs &rarr;</span>
                    </Button>
                  </Link>
                </div>
              </div>
              <div className="lg:col-span-6 bg-[#171717] rounded-2xl p-5 font-mono text-xs text-[#FFF9F2] overflow-x-auto shadow-inner">
                <div className="text-[#FF7A18] font-bold mb-2"># MCP Tool Schema</div>
                <pre>
{`{
  "name": "search_products",
  "description": "Semantic catalog search over local merchants",
  "parameters": {
    "query": "string (required)",
    "pincode": "string (6-digit)"
  }
}`}
                </pre>
              </div>
            </div>
          )}

          {activeTab === "enterprises" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-6 space-y-4">
                <Badge variant="outline" className="text-[10px] text-[#FF7A18] border-[#FFD9A8] bg-[#FFF4E6]">
                  Orchestration Scale
                </Badge>
                <h3 className="text-2xl sm:text-3xl font-black text-[#171717] tracking-tight">
                  Connect LLMs to National Quick Commerce Networks
                </h3>
                <p className="text-xs sm:text-sm text-[#5F5F5F] leading-relaxed">
                  Route orders across Blinkit, Zepto, Amazon, Flipkart, ONDC, and private supplier networks with unified multi-tenant governance and consolidated settlement.
                </p>
                <div className="pt-2">
                  <Link href="/enterprise">
                    <Button className="text-xs font-extrabold">
                      <span>Explore Enterprise Infrastructure &rarr;</span>
                    </Button>
                  </Link>
                </div>
              </div>
              <div className="lg:col-span-6 bg-[#FFF9F2] border border-[#F0DED0] rounded-2xl p-6 space-y-3">
                <div className="text-xs font-bold text-[#171717]">Enterprise Guardrail Guarantees</div>
                <ul className="space-y-2 text-xs text-[#5F5F5F]">
                  <li className="p-3 bg-white rounded-xl border border-[#F0DED0] flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>Multi-tenant tenant isolation and hierarchical quotas</span>
                  </li>
                  <li className="p-3 bg-white rounded-xl border border-[#F0DED0] flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>Immutable append-only cryptographic audit ledger</span>
                  </li>
                  <li className="p-3 bg-white rounded-xl border border-[#F0DED0] flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>High-throughput sub-100ms vector search latency</span>
                  </li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </section>

      <PatternDivider className="max-w-4xl mx-auto my-6" />

      {/* 4. HOW: 5-Step Agentic Commerce Pipeline */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto space-y-3 mb-14">
          <Badge variant="outline" className="text-[11px] font-bold uppercase tracking-wider text-[#FF7A18] border-[#FFD9A8] bg-[#FFF4E6]">
            Architecture &amp; Flow
          </Badge>
          <h2 className="text-3xl sm:text-4xl font-black text-[#171717] tracking-tight">
            How a Prompt Becomes a Physical Delivery
          </h2>
          <p className="text-xs sm:text-sm text-[#5F5F5F]">
            From the moment a user asks an AI assistant for something to the physical handover at the door.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {[
            {
              step: "01",
              title: "Agent Intent",
              desc: "User prompts Claude or ChatGPT: 'Order 1kg fresh organic Alphonso mangoes to my address.'",
              icon: <Sparkles className="w-5 h-5 text-[#FF7A18]" />,
            },
            {
              step: "02",
              title: "Vector Discovery",
              desc: "Qdrant matches query against live catalogs of verified stores within buyer's delivery pincode.",
              icon: <Search className="w-5 h-5 text-[#FF203D]" />,
            },
            {
              step: "03",
              title: "Policy Check",
              desc: "Deterministic engine evaluates price against user's daily budget and per-tx ceiling.",
              icon: <ShieldCheck className="w-5 h-5 text-emerald-600" />,
            },
            {
              step: "04",
              title: "Razorpay Link",
              desc: "Razorpay payment link generated; HMAC cryptographic webhook settles the funds upon checkout.",
              icon: <Lock className="w-5 h-5 text-[#FF203D]" />,
            },
            {
              step: "05",
              title: "Fulfillment",
              desc: "Merchant console buzzes with order details; store marks 'Ready' and hands over to rider.",
              icon: <Truck className="w-5 h-5 text-blue-600" />,
            },
          ].map((s) => (
            <div
              key={s.step}
              className="bg-white rounded-3xl p-6 border border-[#F0DED0] shadow-sm relative overflow-hidden flex flex-col justify-between"
            >
              <div>
                <div className="text-xs font-mono font-bold text-[#FF7A18] mb-3">STEP {s.step}</div>
                <div className="w-10 h-10 rounded-2xl bg-[#FFF4E6] border border-[#FFD9A8] flex items-center justify-center mb-3">
                  {s.icon}
                </div>
                <h3 className="font-extrabold text-sm text-[#171717]">{s.title}</h3>
                <p className="text-xs text-[#5F5F5F] mt-2 leading-relaxed">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <PatternDivider className="max-w-4xl mx-auto my-6" />

      {/* 5. CALL TO ACTION */}
      <section className="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-br from-white via-[#FFF4E6] to-[#FFE8C7] border border-[#FFD9A8] rounded-3xl p-8 sm:p-14 text-center relative overflow-hidden shadow-lg">
          <MandalaAccent className="absolute -top-24 -left-24 w-80 h-80 text-[#FF7A18] opacity-[0.26] pointer-events-none" />
          <MandalaAccent className="absolute -bottom-24 -right-24 w-80 h-80 text-[#FF203D] opacity-[0.26] pointer-events-none" />


          <div className="max-w-3xl mx-auto space-y-6 relative z-10">
            <h2 className="text-3xl sm:text-5xl font-black text-[#171717] tracking-tight">
              Ready to Join the Agentic Commerce Revolution?
            </h2>
            <p className="text-sm sm:text-base text-[#5F5F5F] leading-relaxed max-w-2xl mx-auto font-medium">
              Whether you are a merchant expanding to AI buyers, a developer creating the next autonomous assistant, or an enterprise scaling operations.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
              <Link href="/merchant/register">
                <Button size="lg" className="text-xs sm:text-sm font-extrabold h-12 px-6">
                  <Store className="w-4 h-4 mr-2" />
                  <span>Onboard Your Merchant Store</span>
                </Button>
              </Link>

              <Link href="/user/onboarding">
                <Button size="lg" variant="outline" className="text-xs sm:text-sm font-bold h-12 px-6">
                  <ShieldCheck className="w-4 h-4 mr-2 text-emerald-600" />
                  <span>Set Buyer Guardrails</span>
                </Button>
              </Link>

              <Link href="/developer">
                <Button size="lg" variant="ghost" className="text-xs sm:text-sm font-bold h-12 px-5">
                  <Code className="w-4 h-4 mr-2 text-[#FF7A18]" />
                  <span>View MCP Documentation</span>
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
