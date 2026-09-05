"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Check, Copy, ArrowRight, ArrowLeft, Store, MapPin, Phone, Package, CreditCard, Sparkles } from "lucide-react";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { useToast } from "@/components/ui/Toast";
import { api } from "@/lib/api";
import { PricingType } from "@/lib/types";

export default function MerchantRegisterPage() {
  const { showToast } = useToast();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);

  // Form State
  const [storeName, setStoreName] = useState("");
  const [storeType, setStoreType] = useState("local_merchant");
  const [storeDesc, setStoreDesc] = useState("");
  const [address, setAddress] = useState("");
  const [pincode, setPincode] = useState("");
  const [radius, setRadius] = useState("8");
  const [ownerName, setOwnerName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [prodName, setProdName] = useState("");
  const [pricingType, setPricingType] = useState<PricingType>("fixed_unit");
  const [prodPrice, setProdPrice] = useState("220");
  const [prodUnit, setProdUnit] = useState("piece");
  const [prodMin, setProdMin] = useState("1.0");
  const [prodStep, setProdStep] = useState("1.0");
  const [upi, setUpi] = useState("");
  const [bankAcc, setBankAcc] = useState("");
  const [ifsc, setIfsc] = useState("");

  // Post-registration credentials
  const [createdMerchantId, setCreatedMerchantId] = useState("");
  const [createdApiKey, setCreatedApiKey] = useState("");

  const handlePricingTypeChange = (type: PricingType) => {
    setPricingType(type);
    if (type === "weight_based") {
      setProdUnit("kg");
      setProdMin("0.25");
      setProdStep("0.25");
    } else if (type === "volume_based") {
      setProdUnit("liter");
      setProdMin("0.5");
      setProdStep("0.5");
    } else {
      setProdUnit("piece");
      setProdMin("1.0");
      setProdStep("1.0");
    }
  };

  const handleNext = async () => {
    if (currentStep === 1) {
      if (!storeName.trim()) {
        showToast("Please enter your Store Name.", "error");
        return;
      }
    } else if (currentStep === 2) {
      if (!address.trim() || !pincode.trim()) {
        showToast("Please enter physical address and PIN code.", "error");
        return;
      }
      if (pincode.trim().length !== 6) {
        showToast("PIN code must be a valid 6-digit number.", "error");
        return;
      }
    } else if (currentStep === 3) {
      if (!phone.trim() || !email.trim()) {
        showToast("Please enter phone and email address.", "error");
        return;
      }
    } else if (currentStep === 4) {
      if (!prodName.trim() || !prodPrice.trim()) {
        showToast("Please provide signature product details.", "error");
        return;
      }
    } else if (currentStep === 5) {
      if (!upi.trim()) {
        showToast("Please provide your UPI ID for daily payouts.", "error");
        return;
      }
      // Submit registration
      await submitOnboarding();
      return;
    }

    setCurrentStep((prev) => Math.min(6, prev + 1));
  };

  const handlePrev = () => {
    setCurrentStep((prev) => Math.max(1, prev - 1));
  };

  const submitOnboarding = async () => {
    setLoading(true);
    try {
      // 1. Register Merchant
      const merchant = await api.registerMerchant({
        name: storeName.trim(),
        type: storeType,
        description: storeDesc.trim() || `${storeName} located at ${address}`,
        location: address.trim(),
        pincode: pincode.trim(),
        contact_phone: phone.trim(),
        contact_email: email.trim(),
        business_type: storeType === "marketplace" ? "groceries" : "sweets",
      });

      setCreatedMerchantId(merchant.provider_id);
      const key = merchant.api_key || `sk_live_${merchant.provider_id.slice(0, 16)}`;
      setCreatedApiKey(key);

      // 2. Register Initial Product
      const pricePaise = Math.round(parseFloat(prodPrice || "220") * 100);
      await api.addProduct(merchant.provider_id, {
        name: prodName.trim(),
        category: storeType === "marketplace" ? "general" : "sweets",
        price_amount: pricePaise,
        price_currency: "INR",
        pricing_type: pricingType,
        unit: prodUnit,
        min_quantity: parseFloat(prodMin || "1.0"),
        increment_step: parseFloat(prodStep || "1.0"),
        quantity: 30,
        prep_time_minutes: 15,
        pincode: pincode.trim(),
        availability_status: "in_stock",
        fulfillment_type: "pickup",
      });

      showToast("Store and catalog item provisioned successfully!");
      setCurrentStep(6);
    } catch (err: any) {
      console.error("Onboarding error:", err);
      showToast(err.message || "Registration failed. Please check details.", "error");
    } finally {
      setLoading(false);
    }
  };

  const copyKey = () => {
    navigator.clipboard.writeText(createdApiKey);
    showToast("API Key copied to clipboard!");
  };

  const stepTitles = ["Identity", "Location", "Contact", "Catalog", "Payouts", "Launch"];

  return (
    <div className="min-h-screen flex flex-col bg-[#FFF9F2]">
      <Navbar />

      <main className="flex-1 w-full max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14 flex flex-col items-center justify-center">
        <Card className="w-full p-6 sm:p-10 shadow-xl bg-white">
          
          {/* 6-Step Stepper Progress Bar */}
          <div className="mb-10">
            <div className="flex items-center justify-between relative mb-3">
              {stepTitles.map((title, idx) => {
                const stepNum = idx + 1;
                const isActive = currentStep === stepNum;
                const isCompleted = currentStep > stepNum;

                return (
                  <div key={title} className="flex flex-col items-center relative z-10">
                    <div
                      className={`w-9 h-9 rounded-xl font-black text-xs flex items-center justify-center transition-all ${
                        isActive
                          ? "bg-[#FF203D] text-white shadow-sm ring-4 ring-[#FF203D]/15"
                          : isCompleted
                          ? "bg-[#FF9F1C] text-white"
                          : "bg-[#FFE8C7] text-[#5F5F5F]"
                      }`}
                    >
                      {isCompleted ? <Check className="w-4 h-4" /> : stepNum}
                    </div>
                    <span
                      className={`text-[11px] font-bold mt-2 hidden sm:block ${
                        isActive ? "text-[#171717]" : "text-[#8A8A8A]"
                      }`}
                    >
                      {title}
                    </span>
                  </div>
                );
              })}

              {/* Progress Line */}
              <div className="absolute top-4.5 left-4 right-4 h-1 bg-[#FFE8C7] -z-0 rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#FF203D] transition-all duration-300"
                  style={{ width: `${((currentStep - 1) / 5) * 100}%` }}
                />
              </div>
            </div>
          </div>

          {/* Step Form Panes */}
          <form onSubmit={(e) => e.preventDefault()}>
            
            {/* STEP 1: Store Identity */}
            {currentStep === 1 && (
              <div className="space-y-4 animate-in fade-in">
                <div>
                  <Badge variant="brand" className="mb-2">Step 1 of 6</Badge>
                  <h2 className="text-xl sm:text-2xl font-black text-[#171717]">Store Identity &amp; Category</h2>
                  <p className="text-xs text-[#5F5F5F] mt-1 font-medium">Tell us the brand and category of your commerce establishment.</p>
                </div>
                <Input
                  label="Store Name *"
                  required
                  value={storeName}
                  onChange={(e) => setStoreName(e.target.value)}
                  placeholder="e.g. Haldiram Sweets & Bakery"
                />
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-[#171717]">Business Category *</label>
                  <select
                    value={storeType}
                    onChange={(e) => setStoreType(e.target.value)}
                    className="w-full bg-[#FFF9F2] border border-[#F0DED0] rounded-xl px-3.5 py-2.5 text-xs sm:text-sm text-[#171717] outline-none focus:border-[#FF203D] cursor-pointer"
                  >
                    <option value="local_merchant">Local Merchant / Sweets &amp; Confectionery</option>
                    <option value="local_merchant">Restaurant / Quick Bites</option>
                    <option value="marketplace">Supermarket / Daily Essentials</option>
                    <option value="enterprise">Multi-outlet Enterprise</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-[#171717]">Brief Description</label>
                  <textarea
                    rows={3}
                    value={storeDesc}
                    onChange={(e) => setStoreDesc(e.target.value)}
                    placeholder="Specializes in fresh North Indian sweets, ghee preparations, and traditional savory snacks."
                    className="w-full bg-[#FFF9F2] border border-[#F0DED0] rounded-xl px-3.5 py-2.5 text-xs sm:text-sm text-[#171717] outline-none focus:border-[#FF203D]"
                  />
                </div>
              </div>
            )}

            {/* STEP 2: Location & Serviceability */}
            {currentStep === 2 && (
              <div className="space-y-4 animate-in fade-in">
                <div>
                  <Badge variant="brand" className="mb-2">Step 2 of 6</Badge>
                  <h2 className="text-xl sm:text-2xl font-black text-[#171717]">Location &amp; Serviceability</h2>
                  <p className="text-xs text-[#5F5F5F] mt-1 font-medium">Where is your store physically located and what areas can you serve?</p>
                </div>
                <Input
                  label="Physical Store Address *"
                  required
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="e.g. Shop 14, Main Market, Lajpat Nagar, New Delhi"
                />
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <Input
                    label="Primary PIN Code *"
                    required
                    maxLength={6}
                    value={pincode}
                    onChange={(e) => setPincode(e.target.value)}
                    placeholder="110024"
                  />
                  <div className="space-y-1.5">
                    <label className="block text-xs font-bold text-[#171717]">Delivery Radius</label>
                    <select
                      value={radius}
                      onChange={(e) => setRadius(e.target.value)}
                      className="w-full bg-[#FFF9F2] border border-[#F0DED0] rounded-xl px-3.5 py-2.5 text-xs sm:text-sm text-[#171717] outline-none focus:border-[#FF203D] cursor-pointer"
                    >
                      <option value="5">Within 5 km</option>
                      <option value="8">Within 8 km (Standard)</option>
                      <option value="15">Within 15 km (Citywide)</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* STEP 3: Store Contact & Alerts */}
            {currentStep === 3 && (
              <div className="space-y-4 animate-in fade-in">
                <div>
                  <Badge variant="brand" className="mb-2">Step 3 of 6</Badge>
                  <h2 className="text-xl sm:text-2xl font-black text-[#171717]">Store Contact &amp; Alerts</h2>
                  <p className="text-xs text-[#5F5F5F] mt-1 font-medium">Communication channels for real-time order alerts and settlement summaries.</p>
                </div>
                <Input
                  label="Manager / Owner Name *"
                  required
                  value={ownerName}
                  onChange={(e) => setOwnerName(e.target.value)}
                  placeholder="e.g. Rajesh Sharma"
                />
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <Input
                    label="WhatsApp / Mobile *"
                    required
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+91 98765 43210"
                  />
                  <Input
                    label="Contact Email *"
                    required
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="store@example.com"
                  />
                </div>
              </div>
            )}

            {/* STEP 4: Initial Signature Product */}
            {currentStep === 4 && (
              <div className="space-y-4 animate-in fade-in">
                <div>
                  <Badge variant="brand" className="mb-2">Step 4 of 6</Badge>
                  <h2 className="text-xl sm:text-2xl font-black text-[#171717]">Signature Menu Item</h2>
                  <p className="text-xs text-[#5F5F5F] mt-1 font-medium">Configure your first catalog item with unit, weight, or volume pricing.</p>
                </div>
                <Input
                  label="Signature Item Name *"
                  required
                  value={prodName}
                  onChange={(e) => setProdName(e.target.value)}
                  placeholder="e.g. Motichoor Ladoo or Kaju Katli"
                />
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-[#171717]">Pricing Model</label>
                  <div className="grid grid-cols-3 gap-2">
                    <label
                      className={`flex items-center gap-2 p-2.5 rounded-xl border cursor-pointer text-xs font-bold transition-all ${
                        pricingType === "fixed_unit"
                          ? "border-[#FF203D] bg-[#FFE8C7] text-[#171717]"
                          : "border-[#F0DED0] bg-[#FFF9F2] text-[#5F5F5F]"
                      }`}
                    >
                      <input
                        type="radio"
                        name="pricingType"
                        checked={pricingType === "fixed_unit"}
                        onChange={() => handlePricingTypeChange("fixed_unit")}
                        className="accent-[#FF203D]"
                      />
                      <span>Fixed Unit</span>
                    </label>
                    <label
                      className={`flex items-center gap-2 p-2.5 rounded-xl border cursor-pointer text-xs font-bold transition-all ${
                        pricingType === "weight_based"
                          ? "border-[#FF203D] bg-[#FFE8C7] text-[#171717]"
                          : "border-[#F0DED0] bg-[#FFF9F2] text-[#5F5F5F]"
                      }`}
                    >
                      <input
                        type="radio"
                        name="pricingType"
                        checked={pricingType === "weight_based"}
                        onChange={() => handlePricingTypeChange("weight_based")}
                        className="accent-[#FF203D]"
                      />
                      <span>Weight (₹/kg)</span>
                    </label>
                    <label
                      className={`flex items-center gap-2 p-2.5 rounded-xl border cursor-pointer text-xs font-bold transition-all ${
                        pricingType === "volume_based"
                          ? "border-[#FF203D] bg-[#FFE8C7] text-[#171717]"
                          : "border-[#F0DED0] bg-[#FFF9F2] text-[#5F5F5F]"
                      }`}
                    >
                      <input
                        type="radio"
                        name="pricingType"
                        checked={pricingType === "volume_based"}
                        onChange={() => handlePricingTypeChange("volume_based")}
                        className="accent-[#FF203D]"
                      />
                      <span>Volume (₹/L)</span>
                    </label>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <Input
                    label="Price in INR (₹) *"
                    required
                    type="number"
                    min="1"
                    step="0.5"
                    value={prodPrice}
                    onChange={(e) => setProdPrice(e.target.value)}
                  />
                  <Input
                    label="Unit Label *"
                    value={prodUnit}
                    onChange={(e) => setProdUnit(e.target.value)}
                  />
                </div>

                {pricingType !== "fixed_unit" && (
                  <div className="grid grid-cols-2 gap-3 pt-2 border-t border-[#F0DED0]">
                    <Input
                      label="Min Order Qty (e.g. 0.25)"
                      type="number"
                      step="0.05"
                      value={prodMin}
                      onChange={(e) => setProdMin(e.target.value)}
                    />
                    <Input
                      label="Step Increment (e.g. 0.25)"
                      type="number"
                      step="0.05"
                      value={prodStep}
                      onChange={(e) => setProdStep(e.target.value)}
                    />
                  </div>
                )}
              </div>
            )}

            {/* STEP 5: Daily Settlements */}
            {currentStep === 5 && (
              <div className="space-y-4 animate-in fade-in">
                <div>
                  <Badge variant="brand" className="mb-2">Step 5 of 6</Badge>
                  <h2 className="text-xl sm:text-2xl font-black text-[#171717]">Razorpay Daily Settlements</h2>
                  <p className="text-xs text-[#5F5F5F] mt-1 font-medium">Configure your bank account or UPI VPA for automated payouts.</p>
                </div>
                <Input
                  label="UPI ID / VPA for Instant Payouts *"
                  required
                  value={upi}
                  onChange={(e) => setUpi(e.target.value)}
                  placeholder="storename@okhdfcbank"
                />
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <Input
                    label="Bank Account Number (Optional)"
                    value={bankAcc}
                    onChange={(e) => setBankAcc(e.target.value)}
                    placeholder="123456789012"
                  />
                  <Input
                    label="Bank IFSC Code (Optional)"
                    value={ifsc}
                    onChange={(e) => setIfsc(e.target.value)}
                    placeholder="HDFC0001234"
                  />
                </div>
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center gap-2 font-medium">
                  <span className="font-bold">✓</span>
                  <span>Razorpay 256-bit automated daily batch payout protocol ready.</span>
                </div>
              </div>
            )}

            {/* STEP 6: Launch Terminal */}
            {currentStep === 6 && (
              <div className="space-y-5 text-center py-4 animate-in zoom-in-95">
                <div className="w-16 h-16 rounded-3xl bg-emerald-100 border border-emerald-300 text-emerald-700 flex items-center justify-center text-3xl mx-auto shadow-sm">
                  ✓
                </div>
                <div>
                  <h2 className="text-2xl font-black text-[#171717]">Store Successfully Registered!</h2>
                  <p className="text-xs text-[#5F5F5F] mt-1 max-w-md mx-auto font-medium">
                    Your store is now live in the TransactAI network. Autonomous agents can discover your catalog items immediately.
                  </p>
                </div>

                <div className="p-4 bg-[#FFF9F2] border border-[#F0DED0] rounded-2xl text-left space-y-2 max-w-md mx-auto">
                  <div className="text-[11px] font-mono text-[#5F5F5F] font-bold">Live Merchant API Key:</div>
                  <div className="flex items-center justify-between bg-white px-3 py-2 rounded-xl border border-[#F0DED0]">
                    <span className="font-mono text-xs text-[#FF7A18] font-bold truncate">{createdApiKey}</span>
                    <Button variant="ghost" size="sm" onClick={copyKey} className="ml-2 gap-1 text-xs">
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy</span>
                    </Button>
                  </div>
                </div>

                <div className="pt-4 max-w-md mx-auto">
                  <Link href={`/merchant/dashboard/${createdMerchantId}`} className="w-full block">
                    <Button variant="primary" size="lg" className="w-full font-black text-sm flex items-center justify-center gap-2 shadow-lg">
                      <span>Open Store Operations Terminal</span>
                      <ArrowRight className="w-4 h-4" />
                    </Button>
                  </Link>
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            {currentStep < 6 && (
              <div className="flex items-center justify-between pt-6 mt-8 border-t border-[#F0DED0]">
                <Button
                  variant="outline"
                  size="md"
                  onClick={handlePrev}
                  disabled={currentStep === 1 || loading}
                  className="gap-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back</span>
                </Button>

                <Button
                  variant="primary"
                  size="md"
                  onClick={handleNext}
                  disabled={loading}
                  className="gap-2 font-extrabold"
                >
                  {loading ? (
                    <span>Provisioning Store...</span>
                  ) : currentStep === 5 ? (
                    <span>Complete Onboarding &amp; Launch</span>
                  ) : (
                    <>
                      <span>Continue</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </Button>
              </div>
            )}

          </form>

        </Card>
      </main>

      <Footer />
    </div>
  );
}
