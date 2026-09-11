"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Store,
  Lock,
  Mail,
  Phone,
  ArrowRight,
  ShieldCheck,
  Sparkles,
  KeyRound,
  Building2,
  MapPin,
  CheckCircle2,
} from "lucide-react";
import { api } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Badge from "@/components/ui/Badge";
import MandalaAccent from "@/components/patterns/MandalaAccent";

export default function MerchantLoginPage() {
  const router = useRouter();
  const { showToast } = useToast();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [loading, setLoading] = useState(false);

  // Login form state
  const [loginId, setLoginId] = useState("");
  const [password, setPassword] = useState("");

  // Register form state
  const [regName, setRegName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPhone, setRegPhone] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regBusinessType, setRegBusinessType] = useState("kirana");
  const [regLocation, setRegLocation] = useState("");
  const [regPincode, setRegPincode] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginId.trim() || !password) {
      showToast("Please enter your Login ID and password.", "error");
      return;
    }

    try {
      setLoading(true);
      const res = await api.loginMerchant({
        login_id: loginId.trim(),
        password,
      });

      // Save token and merchant state to localStorage
      localStorage.setItem("transact_merchant_token", res.access_token);
      localStorage.setItem("transact_merchant_user", JSON.stringify(res.merchant));

      showToast(`Welcome back, ${res.merchant.name}!`, "success");
      const targetId = res.merchant.merchant_id || res.merchant.provider_id;
      router.push(`/merchant/dashboard/${targetId}`);
    } catch (err: any) {
      showToast(err.message || "Invalid login credentials", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regName.trim() || !regPassword) {
      showToast("Store name and password are required.", "error");
      return;
    }
    if (!regEmail.trim() && !regPhone.trim()) {
      showToast("Please provide either email or phone number.", "error");
      return;
    }

    try {
      setLoading(true);
      const res = await api.registerMerchantAuth({
        name: regName.trim(),
        contact_email: regEmail.trim() || undefined,
        contact_phone: regPhone.trim() || undefined,
        password: regPassword,
        business_type: regBusinessType,
        location: regLocation.trim() || undefined,
        pincode: regPincode.trim() || undefined,
      });

      localStorage.setItem("transact_merchant_token", res.access_token);
      localStorage.setItem("transact_merchant_user", JSON.stringify(res.merchant));

      showToast(`Store registered! Welcome, ${res.merchant.name}!`, "success");
      const targetId = res.merchant.merchant_id || res.merchant.provider_id;
      router.push(`/merchant/dashboard/${targetId}`);
    } catch (err: any) {
      showToast(err.message || "Registration failed", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = (email: string, name: string) => {
    setMode("login");
    setLoginId(email);
    setPassword("Merchant@2026");
    showToast(`Loaded credentials for ${name}`, "success");
  };

  return (
    <div className="min-h-screen bg-[#FFF9F2] py-12 px-4 sm:px-6 lg:px-8 flex flex-col justify-center relative overflow-hidden">
      {/* Background Motifs */}
      <div className="absolute -left-24 top-12 opacity-25 pointer-events-none">
        <MandalaAccent size={340} className="text-[#FF9F1C]" />
      </div>
      <div className="absolute -right-24 bottom-12 opacity-20 pointer-events-none">
        <MandalaAccent size={320} className="text-[#2EC4B6]" />
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="flex justify-center">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#FF9F1C] to-[#E0533C] flex items-center justify-center shadow-lg shadow-[#FF9F1C]/25 text-white">
            <Store className="w-7 h-7" />
          </div>
        </div>
        <h2 className="mt-4 text-center text-3xl font-black text-[#171717] tracking-tight">
          Merchant Operations Portal
        </h2>
        <p className="mt-1.5 text-center text-sm text-[#737373]">
          Secure multi-tenant inventory & stock verification console
        </p>

        {/* Tab Switcher */}
        <div className="mt-6 flex bg-[#F0ECE1] p-1 rounded-xl">
          <button
            type="button"
            onClick={() => setMode("login")}
            className={`flex-1 py-2 text-sm font-bold rounded-lg transition-all ${
              mode === "login"
                ? "bg-white text-[#171717] shadow-sm"
                : "text-[#737373] hover:text-[#171717]"
            }`}
          >
            Sign In to Store
          </button>
          <button
            type="button"
            onClick={() => setMode("register")}
            className={`flex-1 py-2 text-sm font-bold rounded-lg transition-all ${
              mode === "register"
                ? "bg-white text-[#171717] shadow-sm"
                : "text-[#737373] hover:text-[#171717]"
            }`}
          >
            Register New Vendor
          </button>
        </div>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="bg-white py-8 px-6 sm:px-10 shadow-xl shadow-black/5 rounded-3xl border border-[#E5E0D8]">
          {mode === "login" ? (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#171717] uppercase tracking-wider mb-1.5">
                  Login ID (Email or Phone Number)
                </label>
                <div className="relative">
                  <Input
                    type="text"
                    placeholder="e.g. sharma@kirana.com or +919876543210"
                    value={loginId}
                    onChange={(e) => setLoginId(e.target.value)}
                    required
                    className="w-full pl-10"
                  />
                  <Mail className="w-4 h-4 text-[#A3A3A3] absolute left-3.5 top-3.5" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#171717] uppercase tracking-wider mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <Input
                    type="password"
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full pl-10"
                  />
                  <Lock className="w-4 h-4 text-[#A3A3A3] absolute left-3.5 top-3.5" />
                </div>
              </div>

              <Button
                type="submit"
                variant="primary"
                className="w-full py-3 font-bold flex items-center justify-center gap-2 mt-2"
                disabled={loading}
              >
                {loading ? "Authenticating..." : "Access Store Console"}
                <ArrowRight className="w-4 h-4" />
              </Button>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-[#171717] uppercase tracking-wider mb-1">
                  Store / Vendor Name *
                </label>
                <Input
                  type="text"
                  placeholder="e.g. Gupta Daily Mart"
                  value={regName}
                  onChange={(e) => setRegName(e.target.value)}
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-[#171717] uppercase tracking-wider mb-1">
                    Contact Email
                  </label>
                  <Input
                    type="email"
                    placeholder="store@email.com"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-[#171717] uppercase tracking-wider mb-1">
                    Contact Phone
                  </label>
                  <Input
                    type="tel"
                    placeholder="+919876543210"
                    value={regPhone}
                    onChange={(e) => setRegPhone(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#171717] uppercase tracking-wider mb-1">
                  Password (min 6 characters) *
                </label>
                <Input
                  type="password"
                  placeholder="Create secure store password"
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  required
                  minLength={6}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-[#171717] uppercase tracking-wider mb-1">
                    Business Type
                  </label>
                  <select
                    value={regBusinessType}
                    onChange={(e) => setRegBusinessType(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-white border border-[#E5E0D8] rounded-xl text-[#171717] focus:outline-none focus:ring-2 focus:ring-[#FF9F1C]"
                  >
                    <option value="kirana">Kirana / Grocery</option>
                    <option value="sweets">Sweets & Snacks</option>
                    <option value="pharmacy">Pharmacy</option>
                    <option value="general">General Retail</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-[#171717] uppercase tracking-wider mb-1">
                    Pincode
                  </label>
                  <Input
                    type="text"
                    placeholder="e.g. 110006"
                    value={regPincode}
                    onChange={(e) => setRegPincode(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#171717] uppercase tracking-wider mb-1">
                  Store Address / Location
                </label>
                <Input
                  type="text"
                  placeholder="Market name, Sector, City"
                  value={regLocation}
                  onChange={(e) => setRegLocation(e.target.value)}
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                className="w-full py-3 font-bold flex items-center justify-center gap-2 mt-2"
                disabled={loading}
              >
                {loading ? "Registering Store..." : "Create Merchant Account"}
                <ArrowRight className="w-4 h-4" />
              </Button>
            </form>
          )}

          {/* Quick Demo Logins for Evaluators */}
          <div className="mt-6 pt-5 border-t border-[#F0ECE1]">
            <p className="text-xs font-bold text-[#737373] uppercase tracking-wider text-center mb-3">
              ⚡ Evaluator Quick Test Logins (Password: <code className="text-[#FF9F1C] bg-[#FFF9F2] px-1 py-0.5 rounded">Merchant@2026</code>)
            </p>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleDemoLogin("zepto@quickcommerce.com", "Zepto")}
                className="text-left px-3 py-2 bg-[#F7F4EB] hover:bg-[#EFEAE0] rounded-xl border border-[#E5E0D8] text-xs font-semibold text-[#171717] transition-all flex items-center justify-between"
              >
                <span>⚡ Zepto Quick</span>
                <KeyRound className="w-3 h-3 text-[#FF9F1C]" />
              </button>
              <button
                type="button"
                onClick={() => handleDemoLogin("contact@sharmasweets.in", "Sharma Sweets")}
                className="text-left px-3 py-2 bg-[#F7F4EB] hover:bg-[#EFEAE0] rounded-xl border border-[#E5E0D8] text-xs font-semibold text-[#171717] transition-all flex items-center justify-between"
              >
                <span>🍬 Sharma Sweets</span>
                <KeyRound className="w-3 h-3 text-[#FF9F1C]" />
              </button>
            </div>
          </div>
        </div>

        {/* Back Link */}
        <div className="text-center mt-4">
          <Link
            href="/merchant"
            className="text-xs font-bold text-[#737373] hover:text-[#171717] transition-colors"
          >
            ← Back to Merchant Directory
          </Link>
        </div>
      </div>
    </div>
  );
}
