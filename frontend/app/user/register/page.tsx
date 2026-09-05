"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  User,
  Mail,
  Phone,
  MapPin,
  ShieldCheck,
  ArrowRight,
  Sparkles,
  Lock,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Card from "@/components/ui/Card";
import { useToast } from "@/components/ui/Toast";
import MandalaAccent from "@/components/patterns/MandalaAccent";

export default function UserRegisterPage() {
  const router = useRouter();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    address: "",
    pincode: "560001",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Create user identity in local storage session
      const userId = `user_${formData.name.toLowerCase().replace(/[^a-z0-9]/g, "") || "buyer"}_${Math.random().toString(36).substring(2, 6)}`;
      const userData = {
        user_id: userId,
        name: formData.name,
        email: formData.email,
        phone: formData.phone,
        address: formData.address,
        pincode: formData.pincode,
      };

      localStorage.setItem("transactai_user", JSON.stringify(userData));
      localStorage.setItem("transactai_active_user_id", userId);

      showToast("Account created! Now set your autonomous spending guardrails.");
      router.push("/user/onboarding");
    } catch (err: any) {
      showToast(err.message || "Registration failed", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FFF9F2] flex items-center justify-center p-4 sm:p-8 relative overflow-hidden">
      <MandalaAccent className="absolute -top-24 -right-24 w-80 h-80 text-[#FF7A18] opacity-[0.25] pointer-events-none" />
      <MandalaAccent className="absolute -bottom-24 -left-24 w-80 h-80 text-[#FF203D] opacity-[0.25] pointer-events-none" />


      <div className="w-full max-w-lg relative z-10 space-y-6">
        {/* Header Branding */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FFF4E6] border border-[#FFD9A8] text-xs font-bold text-[#FF7A18] uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Buyer Onboarding</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-[#171717] tracking-tight">
            Empower Your AI Agents to Transact
          </h1>
          <p className="text-xs sm:text-sm text-[#5F5F5F] max-w-md mx-auto">
            Create your shopper profile. You will configure strict financial guardrails before any agent can spend a single rupee.
          </p>
        </div>

        {/* Card Form */}
        <Card className="p-6 sm:p-8 bg-white border-[#F0DED0] shadow-[0_16px_40px_rgba(240,222,208,0.6)]">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-[#171717] mb-1.5">
                Full Name *
              </label>
              <Input
                required
                icon={<User className="w-4 h-4" />}
                placeholder="e.g. Sahil Sharma"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-[#171717] mb-1.5">
                  Email Address *
                </label>
                <Input
                  type="email"
                  required
                  icon={<Mail className="w-4 h-4" />}
                  placeholder="sahil@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#171717] mb-1.5">
                  Contact Phone
                </label>
                <Input
                  type="tel"
                  icon={<Phone className="w-4 h-4" />}
                  placeholder="+91 98765 43210"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-[#171717] mb-1.5">
                Default Delivery Address
              </label>
              <Input
                icon={<MapPin className="w-4 h-4" />}
                placeholder="Flat 402, Royal Residency, Indiranagar"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-[#171717] mb-1.5">
                Delivery Pincode *
              </label>
              <Input
                required
                placeholder="560001"
                value={formData.pincode}
                onChange={(e) => setFormData({ ...formData, pincode: e.target.value })}
              />
              <p className="text-[11px] text-[#8A8A8A] mt-1">
                Used to discover hyper-local instant fulfillment merchants nearby.
              </p>
            </div>

            <div className="pt-2">
              <Button type="submit" isLoading={loading} className="w-full text-xs font-extrabold h-11">
                <span>Continue to Spending Guardrails</span>
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>

            <div className="text-center pt-2">
              <span className="text-xs text-[#5F5F5F]">Already registered? </span>
              <Link
                href="/user/login"
                className="text-xs font-bold text-[#FF7A18] hover:text-[#FF203D] transition-colors"
              >
                Sign in to Dashboard &rarr;
              </Link>
            </div>
          </form>
        </Card>

        {/* Security badge */}
        <div className="text-center flex items-center justify-center gap-1.5 text-xs text-[#8A8A8A]">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Zero unauthorized spend • Hard cryptographic policy verification</span>
        </div>
      </div>
    </div>
  );
}
