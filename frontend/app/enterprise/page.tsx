"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Building2,
  Shield,
  Zap,
  Globe,
  CheckCircle2,
  Lock,
  ArrowRight,
  TrendingUp,
  Cpu,
  Layers,
  Sparkles,
  Send,
  Headphones,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Card from "@/components/ui/Card";
import { useToast } from "@/components/ui/Toast";
import MandalaAccent from "@/components/patterns/MandalaAccent";
import PatternDivider from "@/components/patterns/PatternDivider";

export default function EnterprisePage() {
  const { showToast } = useToast();
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: "",
    email: "",
    company: "",
    volume: "10,000 - 50,000 / month",
    useCase: "Agent Copilot Integration",
    notes: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setSubmitted(true);
      showToast("Thank you! A TransactAI Enterprise Specialist will contact you within 24 hours.");
    }, 600);
  };

  return (
    <div className="min-h-screen bg-[#FFF9F2] text-[#171717] pb-24">
      {/* Hero */}
      <section className="relative pt-20 pb-16 overflow-hidden border-b border-[#F0DED0] bg-white">
        <MandalaAccent className="absolute -top-28 -right-28 w-96 h-96 text-[#FF203D] opacity-[0.25] pointer-events-none" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">

          <div className="max-w-3xl space-y-5">
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#FFF4E6] border border-[#FFD9A8] text-xs font-bold text-[#FF7A18] uppercase tracking-wider">
              <Building2 className="w-3.5 h-3.5" />
              <span>AI Commerce Orchestration Layer</span>
            </div>
            <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-[#171717] leading-tight">
              Scale Autonomous Transactions Across Your Entire Enterprise
            </h1>
            <p className="text-sm sm:text-base text-[#5F5F5F] leading-relaxed">
              TransactAI provides the mission-critical infrastructure required to deploy AI agents that execute real money purchases with 100% deterministic guardrails, zero hallucinated inventory, and automated Razorpay settlements.
            </p>
            <div className="pt-2">
              <a href="#contact">
                <Button size="lg" className="text-xs font-extrabold">
                  <span>Schedule Enterprise Architecture Review</span>
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Enterprise Pillars */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 space-y-20">
        {/* Core Capabilities */}
        <section className="space-y-8">
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <h2 className="text-2xl sm:text-3xl font-black text-[#171717] tracking-tight">
              Enterprise-Grade Autonomous Commerce
            </h2>
            <p className="text-xs sm:text-sm text-[#5F5F5F]">
              Engineered for organizations running thousands of autonomous agents across internal procurement, customer copilots, and quick-commerce integrations.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: <Shield className="w-6 h-6 text-[#FF203D]" />,
                title: "Hierarchical Policy Governance",
                desc: "Enforce departmental spending ceilings, multi-level approval workflows, and mathematical bounds checks before transactions reach the payment gateway.",
              },
              {
                icon: <Globe className="w-6 h-6 text-[#FF7A18]" />,
                title: "Unified Multi-Merchant Routing",
                desc: "Orchestrate fulfillment across quick-commerce providers, national e-commerce marketplaces, ONDC nodes, and verified local merchant networks seamlessly.",
              },
              {
                icon: <Lock className="w-6 h-6 text-emerald-600" />,
                title: "Cryptographic Audit Ledger",
                desc: "Every agent prompt, vector search score, policy validation result, and Razorpay webhook is stored in an immutable, append-only compliance ledger.",
              },
            ].map((p, idx) => (
              <div
                key={idx}
                className="bg-white rounded-3xl p-8 border border-[#F0DED0] shadow-sm space-y-4 hover:border-[#FFD9A8] transition-all"
              >
                <div className="w-12 h-12 rounded-2xl bg-[#FFF4E6] border border-[#FFD9A8] flex items-center justify-center">
                  {p.icon}
                </div>
                <h3 className="font-extrabold text-base text-[#171717]">{p.title}</h3>
                <p className="text-xs text-[#5F5F5F] leading-relaxed">{p.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* High-Throughput Stats */}
        <section className="bg-white rounded-3xl border border-[#F0DED0] p-8 sm:p-12 shadow-sm">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl sm:text-4xl font-black text-[#171717] font-mono">
                &lt; 85ms
              </div>
              <div className="text-xs font-bold text-[#5F5F5F] mt-1">
                Vector Discovery Latency
              </div>
            </div>
            <div>
              <div className="text-3xl sm:text-4xl font-black text-[#FF203D] font-mono">
                0.00%
              </div>
              <div className="text-xs font-bold text-[#5F5F5F] mt-1">
                Hallucinated Transactions
              </div>
            </div>
            <div>
              <div className="text-3xl sm:text-4xl font-black text-[#171717] font-mono">
                99.99%
              </div>
              <div className="text-xs font-bold text-[#5F5F5F] mt-1">
                Uptime SLA
              </div>
            </div>
            <div>
              <div className="text-3xl sm:text-4xl font-black text-[#FF7A18] font-mono">
                100%
              </div>
              <div className="text-xs font-bold text-[#5F5F5F] mt-1">
                Razorpay Automated Settlements
              </div>
            </div>
          </div>
        </section>

        {/* Contact Form Section */}
        <section id="contact" className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
          <div className="lg:col-span-5 space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FFF4E6] border border-[#FFD9A8] text-xs font-bold text-[#FF7A18] uppercase tracking-wider">
              <Headphones className="w-3.5 h-3.5" />
              <span>Talk to TransactAI</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-black text-[#171717] tracking-tight">
              Deploy Autonomous Commerce at Scale
            </h2>
            <p className="text-xs sm:text-sm text-[#5F5F5F] leading-relaxed">
              Connect with our enterprise engineering team to design custom policy engines, high-throughput vector clusters, or private deployment topologies on AWS, Azure, or GCP.
            </p>

            <div className="p-4 rounded-2xl bg-white border border-[#F0DED0] space-y-2 text-xs">
              <div className="font-bold text-[#171717]">What we provide:</div>
              <ul className="space-y-1.5 text-[#5F5F5F]">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Dedicated technical account manager
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Custom MCP schema tailored to your internal LLMs
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Enterprise Razorpay merchant master accounts
                </li>
              </ul>
            </div>
          </div>

          <div className="lg:col-span-7 bg-white rounded-3xl border border-[#F0DED0] p-6 sm:p-8 shadow-sm">
            {submitted ? (
              <div className="py-12 text-center space-y-4">
                <div className="w-14 h-14 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h3 className="text-xl font-extrabold text-[#171717]">
                  Consultation Request Received
                </h3>
                <p className="text-xs text-[#5F5F5F] max-w-sm mx-auto">
                  Thank you, <strong className="text-[#171717]">{form.name}</strong>. An enterprise solution architect will reach out to <strong className="text-[#171717]">{form.email}</strong> shortly.
                </p>
                <Button variant="outline" onClick={() => setSubmitted(false)} className="text-xs">
                  Send Another Inquiry
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-[#171717] mb-1">
                      Your Name *
                    </label>
                    <Input
                      required
                      placeholder="Ananya Verma"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-[#171717] mb-1">
                      Work Email *
                    </label>
                    <Input
                      type="email"
                      required
                      placeholder="ananya@enterprise.com"
                      value={form.email}
                      onChange={(e) => setForm({ ...form, email: e.target.value })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-[#171717] mb-1">
                      Company Name *
                    </label>
                    <Input
                      required
                      placeholder="Enterprise Corp"
                      value={form.company}
                      onChange={(e) => setForm({ ...form, company: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-[#171717] mb-1">
                      Monthly Order Volume
                    </label>
                    <select
                      value={form.volume}
                      onChange={(e) => setForm({ ...form, volume: e.target.value })}
                      className="w-full bg-white border border-[#F0DED0] rounded-xl px-3.5 py-2.5 text-xs text-[#171717] outline-none focus:border-[#FF203D]"
                    >
                      <option>1,000 - 10,000 / month</option>
                      <option>10,000 - 50,000 / month</option>
                      <option>50,000 - 250,000 / month</option>
                      <option>250,000+ / month (Custom Enterprise)</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#171717] mb-1">
                    Primary Use Case
                  </label>
                  <select
                    value={form.useCase}
                    onChange={(e) => setForm({ ...form, useCase: e.target.value })}
                    className="w-full bg-white border border-[#F0DED0] rounded-xl px-3.5 py-2.5 text-xs text-[#171717] outline-none focus:border-[#FF203D]"
                  >
                    <option>Agent Copilot Integration (Claude / Gemini / ChatGPT)</option>
                    <option>Internal Autonomous Procurement & Supply Chain</option>
                    <option>Quick Commerce Gateway (Multi-Merchant Routing)</option>
                    <option>Fintech Autonomous Card / Account Settlement</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#171717] mb-1">
                    Project Requirements / Notes
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Tell us about your transaction infrastructure needs..."
                    value={form.notes}
                    onChange={(e) => setForm({ ...form, notes: e.target.value })}
                    className="w-full bg-white border border-[#F0DED0] rounded-xl p-3 text-xs text-[#171717] placeholder-[#8A8A8A] outline-none focus:border-[#FF203D]"
                  />
                </div>

                <div className="pt-2">
                  <Button type="submit" isLoading={loading} className="w-full text-xs font-extrabold h-11">
                    <Send className="w-4 h-4 mr-1.5" />
                    <span>Submit Architecture Consultation Request</span>
                  </Button>
                </div>
              </form>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
