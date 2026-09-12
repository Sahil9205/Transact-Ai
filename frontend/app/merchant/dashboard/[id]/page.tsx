"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Store,
  Plus,
  RefreshCw,
  ShoppingBag,
  TrendingUp,
  Package,
  Search,
  CheckCircle2,
  Clock,
  ArrowRight,
  Sparkles,
  Layers,
  Bell,
  ChevronRight,
  AlertCircle,
  LogOut,
  Radio,
  Zap,
  Pencil
} from "lucide-react";
import { api } from "@/lib/api";
import { Merchant, Order, Product, DashboardStats } from "@/lib/types";
import { formatINR, cn } from "@/lib/utils";
import { useToast } from "@/components/ui/Toast";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import Badge from "@/components/ui/Badge";
import PatternDivider from "@/components/patterns/PatternDivider";
import MandalaAccent from "@/components/patterns/MandalaAccent";

export default function MerchantDashboardPage() {
  const params = useParams();
  const router = useRouter();
  const { showToast } = useToast();
  const merchantId = (params?.id as string) || "";

  // State
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [merchant, setMerchant] = useState<Merchant | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [catalogSearch, setCatalogSearch] = useState<string>("");
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [pendingPings, setPendingPings] = useState<any[]>([]);
  const [confirmingPingId, setConfirmingPingId] = useState<string | null>(null);
  const [isPulsing, setIsPulsing] = useState(false);
  const [loggedInUser, setLoggedInUser] = useState<any>(null);

  // Check logged-in user on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("transact_merchant_user");
      if (stored) {
        try {
          setLoggedInUser(JSON.parse(stored));
        } catch {
          // ignore
        }
      }
    }
  }, []);

  // Add Modal State
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isSubmittingProduct, setIsSubmittingProduct] = useState(false);
  const [pricingType, setPricingType] = useState<"fixed_unit" | "weight_based" | "volume_based">("fixed_unit");
  const [prodForm, setProdForm] = useState({
    name: "",
    category: "Produce",
    priceInr: "120",
    unit: "piece",
    minQty: "0.25",
    stepQty: "0.25",
    quantity: "25",
    prepTime: "15",
  });

  // Edit Product Modal State
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [isUpdatingProduct, setIsUpdatingProduct] = useState(false);
  const [editPricingType, setEditPricingType] = useState<"fixed_unit" | "weight_based" | "volume_based">("fixed_unit");
  const [editForm, setEditForm] = useState({
    name: "",
    category: "Produce",
    priceInr: "40",
    unit: "piece",
    minQty: "1",
    stepQty: "1",
    quantity: "10",
    description: "",
  });

  // Load Data
  const fetchData = useCallback(async () => {
    if (!merchantId) return;
    try {
      setLoading(true);
      const [statsData, ordersData, pingsData] = await Promise.all([
        api.getDashboardStats(merchantId).catch(() => null),
        api.listMerchantOrders(merchantId).catch(() => []),
        api.getMerchantPings(merchantId, "pending").catch(() => []),
      ]);

      if (statsData) {
        setStats(statsData);
        setMerchant(statsData.merchant);
        setProducts(statsData.products || []);
      } else {
        // Fallback: try direct merchant fetch
        const m = await api.getMerchant(merchantId).catch(() => null);
        if (m) setMerchant(m);
      }

      if (ordersData && ordersData.length > 0) {
        setOrders(ordersData);
      } else if (statsData?.recent_orders) {
        setOrders(statsData.recent_orders);
      }

      setPendingPings(pingsData || []);
    } catch (err: any) {
      console.error("Dashboard fetch error:", err);
      showToast("Unable to load store data. Please retry.", "error");
    } finally {
      setLoading(false);
    }
  }, [merchantId, showToast]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auth Logout
  const handleLogout = () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("transact_merchant_token");
      localStorage.removeItem("transact_merchant_user");
    }
    showToast("Logged out successfully.", "success");
    router.push("/merchant/login");
  };

  // Confirm stock verification ping
  const handleConfirmPing = async (pingId: string) => {
    try {
      setConfirmingPingId(pingId);
      await api.confirmStockPing(merchantId, pingId, { available: true });
      showToast("Stock verified! Freshness timer reset for 6 hours & checkout unblocked.", "success");
      setPendingPings((prev) => prev.filter((p) => p.ping_id !== pingId));
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Failed to confirm stock ping", "error");
    } finally {
      setConfirmingPingId(null);
    }
  };

  // 1-Tap Daily Store Pulse
  const handleStorePulse = async () => {
    try {
      setIsPulsing(true);
      const res = await api.storePulseHeartbeat(merchantId);
      showToast(res.message || "All store catalog items verified fresh today!", "success");
      setPendingPings([]);
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Failed to execute Store Pulse", "error");
    } finally {
      setIsPulsing(false);
    }
  };

  // Operational status toggle (Open ↔ Paused)
  const toggleStoreStatus = async () => {
    if (!merchant) return;
    const current = merchant.operational_status || "open";
    const nextStatus = current === "open" ? "paused" : "open";
    setIsUpdatingStatus(true);

    try {
      await api.updateOperationalStatus(merchant.provider_id, nextStatus);
      setMerchant((prev) => (prev ? { ...prev, operational_status: nextStatus } : null));
      showToast(
        nextStatus === "open"
          ? "Store is now LIVE and accepting orders!"
          : "Store is temporarily PAUSED."
      );
    } catch (err) {
      showToast("Failed to update store operational state", "error");
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  // Toggle single product availability (In Stock ↔ Out of Stock)
  const handleToggleProductAvailability = async (productId: string, currentStatus: string) => {
    const newStatus = currentStatus === "in_stock" ? "out_of_stock" : "in_stock";

    // Optimistic UI update
    setProducts((prev) =>
      prev.map((p) =>
        p.product_id === productId ? { ...p, availability_status: newStatus as any } : p
      )
    );

    try {
      await api.toggleProductAvailability(merchantId, productId, newStatus as any);
      showToast(
        `Item updated to ${newStatus === "in_stock" ? "In Stock" : "Out of Stock"}.`
      );
    } catch (err) {
      // Rollback
      setProducts((prev) =>
        prev.map((p) =>
          p.product_id === productId ? { ...p, availability_status: currentStatus as any } : p
        )
      );
      showToast("Failed to toggle item availability", "error");
    }
  };

  // Adjust product quantity (+/-)
  const handleAdjustQuantity = async (productId: string, delta: number) => {
    const prod = products.find((p) => p.product_id === productId);
    if (!prod) return;

    const currentQty = prod.quantity ?? 0;
    const nextQty = Math.max(0, currentQty + delta);

    // Optimistic update
    setProducts((prev) =>
      prev.map((p) => (p.product_id === productId ? { ...p, quantity: nextQty } : p))
    );

    try {
      await api.adjustProductQuantity(productId, nextQty);
    } catch (err) {
      // Rollback
      setProducts((prev) =>
        prev.map((p) => (p.product_id === productId ? { ...p, quantity: currentQty } : p))
      );
      showToast("Could not adjust stock quantity", "error");
    }
  };

  // Update order fulfillment status
  const handleUpdateOrderStatus = async (orderId: string, newStatus: string) => {
    try {
      await api.updateOrderStatus(orderId, newStatus, merchantId);
      showToast(`Order status updated to ${newStatus.replace("_", " ")}!`);
      // Update local state
      setOrders((prev) =>
        prev.map((o) => (o.order_id === orderId ? { ...o, status: newStatus as any } : o))
      );
      setTimeout(fetchData, 800);
    } catch (err) {
      showToast("Failed to update order status", "error");
    }
  };

  // Submit Add Product
  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!merchantId) return;

    setIsSubmittingProduct(true);
    const priceInr = parseFloat(prodForm.priceInr) || 0;
    const pricePaise = Math.round(priceInr * 100);

    const payload = {
      name: prodForm.name,
      category: prodForm.category,
      price_amount: pricePaise,
      price_currency: "INR",
      pricing_type: pricingType,
      unit: prodForm.unit,
      min_quantity: pricingType === "weight_based" ? parseFloat(prodForm.minQty) : 1.0,
      increment_step: pricingType === "weight_based" ? parseFloat(prodForm.stepQty) : 1.0,
      quantity: parseInt(prodForm.quantity) || 0,
      prep_time_minutes: parseInt(prodForm.prepTime) || 15,
      pincode: merchant?.pincode || "560001",
      availability_status: "in_stock",
      fulfillment_type: "pickup",
    };

    try {
      const created = await api.addProduct(merchantId, payload);
      showToast(`Successfully added ${prodForm.name} to catalog!`);
      setIsAddModalOpen(false);
      setProdForm({
        name: "",
        category: "Produce",
        priceInr: "120",
        unit: "piece",
        minQty: "0.25",
        stepQty: "0.25",
        quantity: "25",
        prepTime: "15",
      });
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Failed to register product", "error");
    } finally {
      setIsSubmittingProduct(false);
    }
  };

  // Open Edit Product Modal with current values
  const openEditModal = (product: Product) => {
    setEditingProduct(product);
    const isWeight = product.pricing_type === "weight_based";
    const isVolume = product.pricing_type === "volume_based";
    const unit = product.unit || (isWeight ? "kg" : isVolume ? "liter" : "piece");
    const priceInr =
      product.price_inr ||
      (product.price_amount ? (product.price_amount / 100).toFixed(2) : "0");
    const pType = (product.pricing_type as "fixed_unit" | "weight_based" | "volume_based") || "fixed_unit";

    setEditPricingType(pType);
    setEditForm({
      name: product.name || "",
      category: product.category || "Produce",
      priceInr: String(priceInr),
      unit: unit,
      minQty: String(product.min_quantity || (isWeight ? "0.25" : "1")),
      stepQty: String(product.increment_step || (isWeight ? "0.25" : "1")),
      quantity: String(product.quantity ?? 0),
      description: product.description || "",
    });
    setIsEditModalOpen(true);
  };

  // Save Product Edit Changes
  const handleSaveProductEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProduct) return;

    setIsUpdatingProduct(true);
    const priceInrNum = parseFloat(editForm.priceInr) || 0;
    const pricePaise = Math.round(priceInrNum * 100);

    const payload = {
      name: editForm.name,
      description: editForm.description || undefined,
      price_amount: pricePaise,
      pricing_type: editPricingType,
      unit: editForm.unit,
      min_quantity:
        editPricingType === "weight_based"
          ? parseFloat(editForm.minQty) || 0.25
          : 1.0,
      increment_step:
        editPricingType === "weight_based"
          ? parseFloat(editForm.stepQty) || 0.25
          : 1.0,
      quantity: parseInt(editForm.quantity, 10) || 0,
    };

    try {
      await api.updateProduct(editingProduct.product_id, payload);
      // Optimistic update in state
      setProducts((prev) =>
        prev.map((p) =>
          p.product_id === editingProduct.product_id
            ? {
                ...p,
                name: editForm.name,
                description: editForm.description,
                price_amount: pricePaise,
                price_inr: priceInrNum.toFixed(2),
                pricing_type: editPricingType as any,
                unit: editForm.unit,
                min_quantity: payload.min_quantity,
                increment_step: payload.increment_step,
                quantity: payload.quantity,
              }
            : p
        )
      );
      showToast(`Updated "${editForm.name}" successfully!`, "success");
      setIsEditModalOpen(false);
    } catch (err: any) {
      showToast(err.message || "Failed to update item", "error");
    } finally {
      setIsUpdatingProduct(false);
    }
  };

  // Filtered Orders
  const filteredOrders = useMemo(() => {
    if (statusFilter === "all") return orders;
    return orders.filter((o) => {
      const s = (o.status || "").toLowerCase();
      if (statusFilter === "discovered") {
        return s === "discovered" || s === "order_created" || s === "payment_success" || s === "pending";
      }
      if (statusFilter === "ready_for_pickup") {
        return s === "ready_for_pickup" || s === "ready";
      }
      if (statusFilter === "completed") {
        return s === "completed" || s === "fulfilled";
      }
      return true;
    });
  }, [orders, statusFilter]);

  // Filtered Catalog
  const filteredCatalog = useMemo(() => {
    const q = catalogSearch.toLowerCase().trim();
    if (!q) return products;
    return products.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        (p.category && p.category.toLowerCase().includes(q))
    );
  }, [products, catalogSearch]);

  const isStoreOpen = (merchant?.operational_status || "open") === "open";

  return (
    <div className="min-h-screen bg-[#FFF9F2] text-[#171717] pb-16">
      {/* Broad Spacious Top Header */}
      <header className="bg-white/95 backdrop-blur-md border-b border-[#F0DED0] sticky top-0 z-30 shadow-[0_2px_12px_rgba(240,222,208,0.45)]">
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 min-h-[82px] py-4 flex items-center justify-between gap-4">
          {/* Store Identity (Clean & Prominent, No Clutter) */}
          <div className="flex items-center gap-4 sm:gap-6">
            <div className="w-12 h-12 rounded-2xl bg-[#FFF4E6] border border-[#FFD9A8] flex items-center justify-center text-[#FF203D] shadow-inner shrink-0">
              <Store className="w-6 h-6" />
            </div>

            <div className="flex flex-col">
              <h1 className="font-extrabold text-xl sm:text-2xl text-[#171717] tracking-tight leading-snug">
                {merchant?.name || "Merchant Store Operations"}
              </h1>
              <div className="text-xs text-[#5F5F5F] flex items-center gap-2 mt-0.5 font-medium">
                <span>{merchant?.location || "Local Storefront"}</span>
                {merchant?.pincode && (
                  <>
                    <span className="text-[#E8CDBB]">&bull;</span>
                    <span className="font-mono">PIN: {merchant.pincode}</span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Operational Header Actions */}
          <div className="flex items-center gap-3 shrink-0">
            {/* Store Status Sliding Toggle (Accepting Orders [Green] ↔ Store Paused [Red]) */}
            <button
              onClick={toggleStoreStatus}
              disabled={isUpdatingStatus}
              role="switch"
              aria-checked={isStoreOpen}
              className={cn(
                "h-10 inline-flex items-center gap-3 px-3.5 rounded-xl text-xs font-bold transition-all border shadow-xs cursor-pointer whitespace-nowrap active:scale-[0.98]",
                isStoreOpen
                  ? "bg-emerald-50/90 border-emerald-300 text-emerald-900 hover:bg-emerald-100/90"
                  : "bg-rose-50/90 border-rose-300 text-rose-900 hover:bg-rose-100/90"
              )}
              title={isStoreOpen ? "Click to Pause Store (stop incoming AI orders)" : "Click to Accept Orders"}
            >
              <span className="flex items-center gap-1.5">
                <span
                  className={cn(
                    "w-2 h-2 rounded-full",
                    isStoreOpen ? "bg-emerald-500 animate-pulse" : "bg-rose-500"
                  )}
                />
                <span>{isStoreOpen ? "Accepting Orders" : "Store Paused"}</span>
              </span>

              {/* Sliding Switch Track & Knob */}
              <span
                className={cn(
                  "relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full p-0.5 transition-colors duration-200 ease-in-out border border-transparent shadow-inner",
                  isStoreOpen ? "bg-emerald-500" : "bg-rose-500"
                )}
              >
                <span
                  className={cn(
                    "pointer-events-none inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out",
                    isStoreOpen ? "translate-x-4" : "translate-x-0"
                  )}
                />
              </span>
            </button>

            {/* Primary Add Item CTA */}
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="h-10 inline-flex items-center gap-2 px-4 sm:px-5 rounded-xl bg-[#FF203D] hover:bg-[#E71937] text-white text-xs font-extrabold transition-all shadow-sm cursor-pointer active:scale-95 whitespace-nowrap"
            >
              <Plus className="w-4 h-4" />
              <span>Add Item</span>
            </button>

            {/* 1-Tap Daily Store Pulse (All Stock Fresh) */}
            <button
              onClick={handleStorePulse}
              disabled={isPulsing}
              title="Confirm all catalog items fresh today (resets 6h timer)"
              className="h-10 inline-flex items-center gap-1.5 px-3.5 rounded-xl bg-amber-50 hover:bg-amber-100 border border-amber-300 text-amber-900 text-xs font-extrabold transition-all shadow-xs cursor-pointer active:scale-95 whitespace-nowrap"
            >
              <Zap className={cn("w-3.5 h-3.5 text-amber-600", isPulsing && "animate-spin")} />
              <span className="hidden sm:inline">{isPulsing ? "Pulsing..." : "Store Pulse"}</span>
            </button>

            {/* Logout Button */}
            <button
              onClick={handleLogout}
              title="Logout from Store Console"
              className="h-10 inline-flex items-center gap-1.5 px-3 rounded-xl bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 text-xs font-bold transition-all shadow-xs cursor-pointer active:scale-95 whitespace-nowrap"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Logout</span>
            </button>

            {/* Refresh Button */}
            <button
              onClick={fetchData}
              title="Refresh Live Data"
              className="w-10 h-10 rounded-xl bg-[#FFF4E6] hover:bg-[#FFE8C7] border border-[#F0DED0] text-[#5F5F5F] hover:text-[#171717] flex items-center justify-center transition-colors cursor-pointer"
            >
              <RefreshCw className={cn("w-4 h-4", loading && "animate-spin text-[#FF7A18]")} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Multi-Tenant Store Isolation Notice */}
        {loggedInUser && loggedInUser.merchant_id !== merchantId && (
          <div className="bg-amber-50 border border-amber-300 rounded-2xl p-4 flex items-center justify-between gap-4 text-amber-900 text-xs shadow-xs">
            <div className="flex items-center gap-2.5">
              <AlertCircle className="w-5 h-5 text-amber-600 shrink-0" />
              <span>
                <strong>Store Notice:</strong> You are logged in as <strong>{loggedInUser.name}</strong>, but viewing <strong>{merchant?.name}</strong>.
              </span>
            </div>
            <Link
              href={`/merchant/dashboard/${loggedInUser.merchant_id}`}
              className="bg-amber-600 hover:bg-amber-700 text-white font-bold px-3 py-1.5 rounded-lg shrink-0 transition-colors"
            >
              Go to My Store
            </Link>
          </div>
        )}

        {/* Live Customer Stock Verification Inquiries Banner (6-Hour Staleness Guardrail Alert) */}
        {pendingPings.length > 0 && (
          <div className="bg-gradient-to-r from-[#FFF0EB] to-[#FFF5EC] border-2 border-[#FF7A18]/40 rounded-3xl p-5 shadow-sm space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2.5 text-[#FF203D] font-extrabold text-sm tracking-tight">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500" />
                </span>
                <span>Active Customer Stock Inquiries ({pendingPings.length})</span>
                <span className="text-[11px] font-bold bg-[#FF203D]/10 text-[#FF203D] px-2 py-0.5 rounded-full border border-[#FF203D]/20">
                  6-Hour Guardrail Triggered
                </span>
              </div>
              <span className="text-xs text-[#737373]">
                AI checkout is currently paused for these items until vendor confirms stock.
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {pendingPings.map((ping) => (
                <div
                  key={ping.ping_id}
                  className="bg-white rounded-2xl p-3.5 border border-[#F0DED0] flex items-center justify-between gap-3 shadow-xs"
                >
                  <div className="flex flex-col">
                    <span className="font-extrabold text-sm text-[#171717]">{ping.product_name}</span>
                    <span className="text-xs text-[#5F5F5F] flex items-center gap-2 mt-0.5">
                      <span>Requested: {ping.requested_quantity} units</span>
                      <span>&bull;</span>
                      <span className="text-amber-600 font-bold">Stock Unverified &gt; 6h</span>
                    </span>
                  </div>
                  <button
                    onClick={() => handleConfirmPing(ping.ping_id)}
                    disabled={confirmingPingId === ping.ping_id}
                    className="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-sm transition-all active:scale-95 shrink-0 flex items-center gap-1.5 cursor-pointer"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>{confirmingPingId === ping.ping_id ? "Confirming..." : "Confirm In Stock"}</span>
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* KPI Bento Grid */}
        <section className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          {/* Revenue */}
          <div className="bg-white rounded-3xl p-6 border border-[#F0DED0] shadow-sm relative overflow-hidden group hover:border-[#FFD9A8] transition-all">
            <div className="flex items-center justify-between text-[#5F5F5F] text-xs">
              <span className="font-bold flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4 text-[#FF7A18]" />
                Total Settled GMV
              </span>
              <span className="text-emerald-700 font-mono text-[11px] bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full font-bold">
                Razorpay Live
              </span>
            </div>
            <div className="mt-4">
              <div className="text-3xl font-black text-[#171717] font-mono tracking-tight">
                {formatINR(stats?.total_revenue_inr ?? 0)}
              </div>
              <div className="text-xs text-[#5F5F5F] mt-1.5 flex items-center gap-1.5 font-medium">
                <span className="text-emerald-700 font-bold">100% automated</span> settlements to merchant bank
              </div>
            </div>
          </div>

          {/* Orders (No "ai commerce" tag, as requested) */}
          <div className="bg-white rounded-3xl p-6 border border-[#F0DED0] shadow-sm relative overflow-hidden group hover:border-[#FFD9A8] transition-all">
            <div className="flex items-center justify-between text-[#5F5F5F] text-xs">
              <span className="font-bold flex items-center gap-1.5">
                <ShoppingBag className="w-4 h-4 text-[#FF203D]" />
                Total Orders
              </span>
            </div>
            <div className="mt-4">
              <div className="text-3xl font-black text-[#171717] font-mono tracking-tight">
                {stats?.total_orders ?? orders.length}
              </div>
              <div className="text-xs text-[#5F5F5F] mt-1.5 font-medium">
                Customer orders fulfilled successfully
              </div>
            </div>
          </div>

          {/* Catalog SKUs */}
          <div className="bg-white rounded-3xl p-6 border border-[#F0DED0] shadow-sm relative overflow-hidden group hover:border-[#FFD9A8] transition-all">
            <div className="flex items-center justify-between text-[#5F5F5F] text-xs">
              <span className="font-bold flex items-center gap-1.5">
                <Package className="w-4 h-4 text-[#FF9F1C]" />
                Catalog SKUs
              </span>
              <span className="text-[#171717] font-mono text-[11px] bg-[#FFF4E6] border border-[#F0DED0] px-2.5 py-0.5 rounded-full font-bold">
                Active Inventory
              </span>
            </div>
            <div className="mt-4">
              <div className="text-3xl font-black text-[#171717] font-mono tracking-tight">
                {products.length}
              </div>
              <div className="text-xs text-[#5F5F5F] mt-1.5 font-medium">
                Configured catalog items & variations
              </div>
            </div>
          </div>
        </section>

        {/* Main Operational Workspace: Orders Feed + Product Catalog */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* COLUMN A: Live Incoming Orders (7 cols) - NO PLATFORM COLUMN */}
          <div className="lg:col-span-7 bg-white rounded-3xl border border-[#F0DED0] overflow-hidden flex flex-col shadow-sm">
            {/* Header & Filter Pills */}
            <div className="p-6 border-b border-[#F0DED0] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-lg font-extrabold text-[#171717] flex items-center gap-2">
                  <span>Live Incoming Orders</span>
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                </h2>
                <p className="text-xs text-[#5F5F5F] mt-1">
                  Real-time incoming customer orders ready for store fulfillment
                </p>
              </div>

              {/* Status Filter Tabs */}
              <div className="flex items-center gap-1 bg-[#FFF4E6] p-1 rounded-xl border border-[#F0DED0] text-xs shrink-0">
                {[
                  { id: "all", label: "All" },
                  { id: "discovered", label: "New" },
                  { id: "ready_for_pickup", label: "Ready" },
                  { id: "completed", label: "Completed" },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setStatusFilter(tab.id)}
                    className={cn(
                      "px-3 py-1 rounded-lg font-bold transition-all text-xs cursor-pointer",
                      statusFilter === tab.id
                        ? "bg-[#FF203D] text-white shadow-xs"
                        : "text-[#5F5F5F] hover:text-[#171717]"
                    )}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Orders Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-[#FFF9F2] border-b border-[#F0DED0] text-[11px] uppercase tracking-wider text-[#5F5F5F] font-bold">
                    <th className="px-5 py-3.5 font-mono">Order ID</th>
                    <th className="px-5 py-3.5">Ordered Item &amp; Qty</th>
                    <th className="px-5 py-3.5">Destination</th>
                    <th className="px-5 py-3.5">Amount</th>
                    <th className="px-5 py-3.5">Status</th>
                    <th className="px-5 py-3.5 text-right">Fulfillment</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F0DED0] text-xs">
                  {filteredOrders.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-5 py-12 text-center text-[#5F5F5F]">
                        <ShoppingBag className="w-8 h-8 text-[#FFD9A8] mx-auto mb-2 opacity-60" />
                        <p className="font-bold text-sm text-[#171717]">No orders in this view</p>
                        <p className="text-xs text-[#8A8A8A] mt-1">
                          New orders placed by buyers will instantly appear here.
                        </p>
                      </td>
                    </tr>
                  ) : (
                    filteredOrders.map((order) => {
                      const isReady = order.status === "ready_for_pickup";
                      const isCompleted = order.status === "completed";

                      const isNew =
                        !isReady &&
                        !isCompleted &&
                        order.status !== "failed" &&
                        order.status !== "cancelled";

                      const matchedProduct = products.find(
                        (p) => p.product_id === order.product_id
                      );
                      const itemName =
                        order.product_name || matchedProduct?.name || "Order Item";
                      const itemUnit = matchedProduct?.unit || "piece";
                      const itemQty = order.quantity || 1;

                      return (
                        <tr
                          key={order.order_id}
                          className="hover:bg-[#FFF9F2]/60 transition-colors"
                        >
                          <td className="px-5 py-4 font-mono font-bold text-[#171717]">
                            #{order.order_id.slice(0, 8)}
                          </td>
                          <td className="px-5 py-4">
                            <div className="flex items-center gap-2.5">
                              <span className="inline-flex items-center justify-center bg-[#FFF4E6] text-[#FF203D] font-mono font-black text-xs px-2 py-1 rounded-lg border border-[#FFD9A8] shrink-0 shadow-2xs">
                                {itemQty}x
                              </span>
                              <div>
                                <span className="font-extrabold text-xs text-[#171717] block leading-tight">
                                  {itemName}
                                </span>
                                <span className="text-[10px] text-[#8A8A8A] font-medium">
                                  {matchedProduct?.category ? `${matchedProduct.category} • ` : ""}per {itemUnit}
                                </span>
                              </div>
                            </div>
                          </td>
                          <td className="px-5 py-4">
                            <div className="font-semibold text-[#171717]">
                              {order.delivery_address || "Local Delivery"}
                            </div>
                            <div className="text-[10px] text-[#5F5F5F] font-mono mt-0.5">
                              PIN: {order.pincode || merchant?.pincode || "—"}
                            </div>
                          </td>
                          <td className="px-5 py-4 font-mono font-bold text-[#171717]">
                            {formatINR(
                              order.total_amount_inr ??
                                (order.total_amount ? order.total_amount / 100 : 0)
                            )}
                          </td>
                          <td className="px-5 py-4">
                            <span
                              className={cn(
                                "px-2.5 py-1 rounded-full text-[10px] font-bold border inline-block uppercase tracking-wider",
                                isCompleted
                                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                  : isReady
                                  ? "bg-amber-50 text-amber-800 border-amber-200"
                                  : "bg-blue-50 text-blue-700 border-blue-200"
                              )}
                            >
                              {(order.status || "new").replace(/_/g, " ")}
                            </span>
                          </td>
                          <td className="px-5 py-4 text-right">
                            {isNew && (
                              <button
                                onClick={() =>
                                  handleUpdateOrderStatus(order.order_id, "ready_for_pickup")
                                }
                                className="px-3 py-1.5 rounded-xl bg-[#FFF4E6] hover:bg-[#FFE8C7] border border-[#FFD9A8] text-[#FF7A18] font-bold text-xs transition-all cursor-pointer shadow-2xs hover:scale-105 active:scale-95"
                              >
                                Mark Ready &rarr;
                              </button>
                            )}
                            {isReady && (
                              <button
                                onClick={() =>
                                  handleUpdateOrderStatus(order.order_id, "completed")
                                }
                                className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition-all cursor-pointer shadow-xs active:scale-95"
                              >
                                Hand to Rider &rarr;
                              </button>
                            )}
                            {isCompleted && (
                              <span className="text-xs font-bold text-emerald-700 inline-flex items-center gap-1">
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                Fulfilled
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* COLUMN B: Store Catalog & Stock Management (5 cols) */}
          <div className="lg:col-span-5 bg-white rounded-3xl border border-[#F0DED0] overflow-hidden flex flex-col shadow-sm">
            {/* Catalog Header */}
            <div className="p-6 border-b border-[#F0DED0] flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-extrabold text-[#171717]">Store Catalog & Stock</h2>
                <p className="text-xs text-[#5F5F5F] mt-1">
                  Manage live prices, stock counters, and availability
                </p>
              </div>
              <button
                onClick={() => setIsAddModalOpen(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#FFF4E6] hover:bg-[#FFE8C7] text-[#171717] text-xs font-bold border border-[#F0DED0] transition-all cursor-pointer shadow-2xs"
              >
                <Plus className="w-3.5 h-3.5 text-[#FF203D]" />
                <span>Add Item</span>
              </button>
            </div>

            {/* Catalog Search Bar */}
            <div className="px-5 py-3 border-b border-[#F0DED0] bg-[#FFF9F2]">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[#8A8A8A]" />
                <input
                  type="text"
                  value={catalogSearch}
                  onChange={(e) => setCatalogSearch(e.target.value)}
                  placeholder="Search catalog items..."
                  className="w-full bg-white border border-[#F0DED0] text-xs text-[#171717] placeholder-[#8A8A8A] rounded-xl pl-8 pr-3 py-2 outline-none focus:border-[#FF203D] focus:ring-1 focus:ring-[#FF203D] transition-colors font-medium"
                />
              </div>
            </div>

            {/* Catalog Table */}
            <div className="overflow-x-auto max-h-[580px] overflow-y-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-[#FFF9F2] border-b border-[#F0DED0] text-[11px] uppercase tracking-wider text-[#5F5F5F] font-bold sticky top-0 z-10 backdrop-blur-sm">
                    <th className="px-4 py-3">Item &amp; Pricing</th>
                    <th className="px-3 py-3 text-center">Stock</th>
                    <th className="px-4 py-3 text-right">Availability &amp; Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F0DED0] text-xs">
                  {filteredCatalog.length === 0 ? (
                    <tr>
                      <td colSpan={3} className="px-4 py-10 text-center text-[#5F5F5F]">
                        <Package className="w-7 h-7 text-[#FFD9A8] mx-auto mb-2 opacity-60" />
                        <p className="font-semibold text-xs text-[#171717]">No items found</p>
                      </td>
                    </tr>
                  ) : (
                    filteredCatalog.map((item) => {
                      const inStock = item.availability_status === "in_stock";
                      const isWeight = item.pricing_type === "weight_based";
                      const unit = item.unit || (isWeight ? "kg" : "piece");
                      const price =
                        item.price_inr ||
                        (item.price_amount ? (item.price_amount / 100).toFixed(2) : "0.00");

                      return (
                        <tr
                          key={item.product_id}
                          className="hover:bg-[#FFF4E6]/40 transition-colors"
                        >
                          {/* Col 1: Item & Price */}
                          <td className="px-4 py-3.5">
                            <div className="font-extrabold text-xs text-[#171717] leading-snug">
                              {item.name}
                            </div>
                            <div className="flex items-center gap-1.5 mt-1">
                              <span className="text-[10px] text-[#5F5F5F] uppercase tracking-wider font-bold bg-[#FFF4E6] px-1.5 py-0.5 rounded border border-[#FFD9A8]/60">
                                {item.category || "General"}
                              </span>
                              <span className="text-[#D1C7BD]">&bull;</span>
                              <span className="font-mono font-black text-xs text-[#FF203D]">
                                ₹{price} <span className="text-[10px] text-[#5F5F5F] font-medium">/{unit}</span>
                              </span>
                            </div>
                            {isWeight && (
                              <div className="text-[10px] text-[#FF7A18] font-mono mt-0.5">
                                Min: {item.min_quantity || 0.25} {unit}
                              </div>
                            )}
                          </td>

                          {/* Col 2: Stock Counter */}
                          <td className="px-3 py-3.5 text-center">
                            <div className="inline-flex items-center gap-1 bg-[#FFF9F2] border border-[#F0DED0] px-1.5 py-1 rounded-lg font-mono text-xs shadow-2xs">
                              <button
                                type="button"
                                onClick={() => handleAdjustQuantity(item.product_id, -1)}
                                className="w-5 h-5 rounded flex items-center justify-center text-[#5F5F5F] hover:text-[#171717] hover:bg-[#FFE8C7] font-bold text-sm cursor-pointer transition-colors"
                                title="Decrease stock"
                              >
                                −
                              </button>
                              <span className="text-[#171717] font-bold w-6 text-center font-mono text-xs">
                                {item.quantity ?? 0}
                              </span>
                              <button
                                type="button"
                                onClick={() => handleAdjustQuantity(item.product_id, 1)}
                                className="w-5 h-5 rounded flex items-center justify-center text-[#5F5F5F] hover:text-[#171717] hover:bg-[#FFE8C7] font-bold text-sm cursor-pointer transition-colors"
                                title="Increase stock"
                              >
                                +
                              </button>
                            </div>
                          </td>

                          {/* Col 3: Availability Toggle + Edit Button */}
                          <td className="px-4 py-3.5 text-right">
                            <div className="inline-flex items-center justify-end gap-2.5">
                              {/* Edit Modal Trigger */}
                              <button
                                type="button"
                                onClick={() => openEditModal(item)}
                                className="p-1.5 rounded-lg bg-[#FFF4E6] hover:bg-[#FFE8C7] border border-[#FFD9A8] text-[#FF7A18] hover:text-[#FF203D] transition-all cursor-pointer shadow-2xs hover:scale-105 active:scale-95"
                                title="Edit item price, unit, or stock count"
                              >
                                <Pencil className="w-3.5 h-3.5" />
                              </button>

                              {/* Sliding Toggle Switch with Label */}
                              <div className="inline-flex items-center gap-1.5">
                                <span
                                  className={cn(
                                    "text-[10px] font-bold whitespace-nowrap",
                                    inStock ? "text-emerald-700" : "text-rose-600"
                                  )}
                                >
                                  {inStock ? "In Stock" : "Out"}
                                </span>
                                <button
                                  type="button"
                                  role="switch"
                                  aria-checked={inStock}
                                  onClick={() =>
                                    handleToggleProductAvailability(
                                      item.product_id,
                                      item.availability_status
                                    )
                                  }
                                  className={cn(
                                    "relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full p-0.5 transition-colors duration-200 ease-in-out shadow-inner focus:outline-hidden",
                                    inStock
                                      ? "bg-emerald-500 hover:bg-emerald-600"
                                      : "bg-rose-500 hover:bg-rose-600"
                                  )}
                                  title={
                                    inStock
                                      ? "Click to mark Out of Stock"
                                      : "Click to mark In Stock"
                                  }
                                >
                                  <span
                                    aria-hidden="true"
                                    className={cn(
                                      "pointer-events-none inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow-sm transition duration-200 ease-in-out",
                                      inStock ? "translate-x-4" : "translate-x-0"
                                    )}
                                  />
                                </button>
                              </div>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>

      {/* Dynamic Add Product Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Add Menu / Catalog Item"
        size="lg"
      >
        <form onSubmit={handleCreateProduct} className="space-y-4">
          <p className="text-xs text-[#5F5F5F] -mt-2">
            Register items with flexible pricing models (unit, weight-based groceries, or volume).
          </p>

          <div>
            <label className="block text-xs font-bold text-[#171717] mb-1">
              Item Name *
            </label>
            <Input
              required
              placeholder="e.g. Alphonso Mangoes, Farm Fresh Paneer, Filter Coffee"
              value={prodForm.name}
              onChange={(e) => setProdForm({ ...prodForm, name: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-[#171717] mb-1">Category *</label>
              <select
                value={prodForm.category}
                onChange={(e) => setProdForm({ ...prodForm, category: e.target.value })}
                className="w-full bg-white border border-[#F0DED0] rounded-xl px-3.5 py-2.5 text-xs text-[#171717] outline-none focus:border-[#FF203D] focus:ring-1 focus:ring-[#FF203D]"
              >
                <option value="Produce">Produce / Fruits & Veg</option>
                <option value="Dairy">Dairy & Eggs</option>
                <option value="Bakery">Bakery & Snacks</option>
                <option value="Beverages">Beverages & Tea</option>
                <option value="Meals">Cooked Meals & Mains</option>
                <option value="Staples">Grains & Staples</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-[#171717] mb-1">
                Pricing Structure *
              </label>
              <div className="grid grid-cols-3 gap-1.5 p-1 bg-[#FFF4E6] border border-[#F0DED0] rounded-xl text-xs font-semibold text-center">
                {[
                  { id: "fixed_unit", label: "Fixed Unit" },
                  { id: "weight_based", label: "Weight" },
                  { id: "volume_based", label: "Volume" },
                ].map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => {
                      setPricingType(t.id as any);
                      if (t.id === "weight_based") setProdForm({ ...prodForm, unit: "kg" });
                      if (t.id === "volume_based") setProdForm({ ...prodForm, unit: "liter" });
                      if (t.id === "fixed_unit") setProdForm({ ...prodForm, unit: "piece" });
                    }}
                    className={cn(
                      "py-1.5 rounded-lg transition-all text-xs font-bold",
                      pricingType === t.id
                        ? "bg-[#FF203D] text-white shadow-2xs"
                        : "text-[#5F5F5F] hover:text-[#171717]"
                    )}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="p-4 bg-[#FFF9F2] border border-[#F0DED0] rounded-2xl space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-[#171717] mb-1">
                  Price (in ₹) *
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-[#5F5F5F] text-xs font-mono font-bold">
                    ₹
                  </span>
                  <input
                    type="number"
                    step="0.5"
                    required
                    min="1"
                    placeholder="120"
                    value={prodForm.priceInr}
                    onChange={(e) => setProdForm({ ...prodForm, priceInr: e.target.value })}
                    className="w-full bg-white border border-[#F0DED0] rounded-xl pl-7 pr-3 py-2 text-xs text-[#171717] font-mono outline-none focus:border-[#FF203D] font-bold"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#171717] mb-1">
                  Unit of Measure *
                </label>
                <Input
                  required
                  placeholder="piece, kg, g, liter"
                  value={prodForm.unit}
                  onChange={(e) => setProdForm({ ...prodForm, unit: e.target.value })}
                />
              </div>
            </div>

            {pricingType === "weight_based" && (
              <div className="grid grid-cols-2 gap-3 pt-2 border-t border-[#F0DED0]">
                <div>
                  <label className="block text-[11px] font-semibold text-[#5F5F5F] mb-1">
                    Min Order Qty (e.g. 0.25 kg)
                  </label>
                  <input
                    type="number"
                    step="0.05"
                    min="0.01"
                    value={prodForm.minQty}
                    onChange={(e) => setProdForm({ ...prodForm, minQty: e.target.value })}
                    className="w-full bg-white border border-[#F0DED0] rounded-xl px-3 py-2 text-xs text-[#171717] font-mono outline-none focus:border-[#FF203D]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[#5F5F5F] mb-1">
                    Step Increment (e.g. 0.25 kg)
                  </label>
                  <input
                    type="number"
                    step="0.05"
                    min="0.01"
                    value={prodForm.stepQty}
                    onChange={(e) => setProdForm({ ...prodForm, stepQty: e.target.value })}
                    className="w-full bg-white border border-[#F0DED0] rounded-xl px-3 py-2 text-xs text-[#171717] font-mono outline-none focus:border-[#FF203D]"
                  />
                </div>
              </div>
            )}

            <div className="text-[11px] text-[#FF7A18] font-bold">
              Configured: ₹{prodForm.priceInr || 0} / {prodForm.unit}
              {pricingType === "weight_based" && ` (min order ${prodForm.minQty}${prodForm.unit})`}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-[#171717] mb-1">
                Initial Stock Count
              </label>
              <input
                type="number"
                min="0"
                value={prodForm.quantity}
                onChange={(e) => setProdForm({ ...prodForm, quantity: e.target.value })}
                className="w-full bg-[#FFF9F2] border border-[#F0DED0] rounded-xl px-3 py-2 text-xs text-[#171717] font-mono outline-none focus:border-[#FF203D]"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-[#171717] mb-1">
                Prep Time (minutes)
              </label>
              <input
                type="number"
                min="0"
                value={prodForm.prepTime}
                onChange={(e) => setProdForm({ ...prodForm, prepTime: e.target.value })}
                className="w-full bg-[#FFF9F2] border border-[#F0DED0] rounded-xl px-3 py-2 text-xs text-[#171717] font-mono outline-none focus:border-[#FF203D]"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#F0DED0]">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsAddModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" isLoading={isSubmittingProduct}>
              Save to Catalog
            </Button>
          </div>
        </form>
      </Modal>

      {/* Dynamic Edit Product Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Edit Catalog Item & Pricing"
        size="lg"
      >
        <form onSubmit={handleSaveProductEdit} className="space-y-4">
          <p className="text-xs text-[#5F5F5F] -mt-2">
            Update pricing, per-piece/per-kg/cup unit of measurement, and live stock count.
          </p>

          <div>
            <label className="block text-xs font-bold text-[#171717] mb-1">
              Item Name *
            </label>
            <Input
              required
              placeholder="e.g. Samosa, Desi Ghee, Masala Chai"
              value={editForm.name}
              onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-[#171717] mb-1">Category</label>
              <select
                value={editForm.category}
                onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                className="w-full bg-white border border-[#F0DED0] rounded-xl px-3.5 py-2.5 text-xs text-[#171717] outline-none focus:border-[#FF203D] focus:ring-1 focus:ring-[#FF203D]"
              >
                <option value="Produce">Produce / Fruits &amp; Veg</option>
                <option value="Dairy">Dairy &amp; Eggs</option>
                <option value="Bakery">Bakery &amp; Snacks</option>
                <option value="Beverages">Beverages &amp; Tea</option>
                <option value="Meals">Cooked Meals &amp; Mains</option>
                <option value="Staples">Grains &amp; Staples</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-[#171717] mb-1">
                Pricing Structure *
              </label>
              <div className="grid grid-cols-3 gap-1.5 p-1 bg-[#FFF4E6] border border-[#F0DED0] rounded-xl text-xs font-semibold text-center">
                {[
                  { id: "fixed_unit", label: "Fixed Unit" },
                  { id: "weight_based", label: "Weight" },
                  { id: "volume_based", label: "Volume" },
                ].map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => {
                      setEditPricingType(t.id as any);
                      if (t.id === "weight_based" && editForm.unit === "piece") setEditForm({ ...editForm, unit: "kg" });
                      if (t.id === "volume_based" && editForm.unit === "piece") setEditForm({ ...editForm, unit: "liter" });
                    }}
                    className={cn(
                      "py-1.5 rounded-lg transition-all text-xs font-bold",
                      editPricingType === t.id
                        ? "bg-[#FF203D] text-white shadow-2xs"
                        : "text-[#5F5F5F] hover:text-[#171717]"
                    )}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="p-4 bg-[#FFF9F2] border border-[#F0DED0] rounded-2xl space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-[#171717] mb-1">
                  Price (in ₹) *
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-[#5F5F5F] text-xs font-mono font-bold">
                    ₹
                  </span>
                  <input
                    type="number"
                    step="0.5"
                    required
                    min="1"
                    placeholder="40"
                    value={editForm.priceInr}
                    onChange={(e) => setEditForm({ ...editForm, priceInr: e.target.value })}
                    className="w-full bg-white border border-[#F0DED0] rounded-xl pl-7 pr-3 py-2 text-xs text-[#171717] font-mono outline-none focus:border-[#FF203D] font-bold"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#171717] mb-1">
                  Unit of Measure *
                </label>
                <Input
                  required
                  placeholder="e.g. piece, kg, cup, box, plate, packet, liter"
                  value={editForm.unit}
                  onChange={(e) => setEditForm({ ...editForm, unit: e.target.value })}
                />
              </div>
            </div>

            {/* Quick Unit Presets */}
            <div>
              <div className="text-[10px] text-[#8A8A8A] font-semibold mb-1.5 uppercase tracking-wider">
                Quick Preset Units:
              </div>
              <div className="flex flex-wrap gap-1.5">
                {["piece", "kg", "cup", "box", "plate", "packet", "liter", "g", "bottle"].map((presetUnit) => (
                  <button
                    key={presetUnit}
                    type="button"
                    onClick={() => {
                      setEditForm({ ...editForm, unit: presetUnit });
                      if (presetUnit === "kg" || presetUnit === "g") setEditPricingType("weight_based");
                      else if (presetUnit === "liter") setEditPricingType("volume_based");
                      else setEditPricingType("fixed_unit");
                    }}
                    className={cn(
                      "px-2 py-0.5 rounded-lg text-[11px] font-bold border transition-all cursor-pointer",
                      editForm.unit.toLowerCase() === presetUnit
                        ? "bg-[#FF203D] text-white border-[#FF203D] shadow-xs"
                        : "bg-white text-[#5F5F5F] border-[#F0DED0] hover:bg-[#FFF4E6] hover:text-[#171717]"
                    )}
                  >
                    {presetUnit}
                  </button>
                ))}
              </div>
            </div>

            {editPricingType === "weight_based" && (
              <div className="grid grid-cols-2 gap-3 pt-2 border-t border-[#F0DED0]">
                <div>
                  <label className="block text-[11px] font-semibold text-[#5F5F5F] mb-1">
                    Min Order Qty ({editForm.unit})
                  </label>
                  <input
                    type="number"
                    step="0.05"
                    min="0.01"
                    value={editForm.minQty}
                    onChange={(e) => setEditForm({ ...editForm, minQty: e.target.value })}
                    className="w-full bg-white border border-[#F0DED0] rounded-xl px-3 py-2 text-xs text-[#171717] font-mono outline-none focus:border-[#FF203D]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[#5F5F5F] mb-1">
                    Step Increment ({editForm.unit})
                  </label>
                  <input
                    type="number"
                    step="0.05"
                    min="0.01"
                    value={editForm.stepQty}
                    onChange={(e) => setEditForm({ ...editForm, stepQty: e.target.value })}
                    className="w-full bg-white border border-[#F0DED0] rounded-xl px-3 py-2 text-xs text-[#171717] font-mono outline-none focus:border-[#FF203D]"
                  />
                </div>
              </div>
            )}

            <div className="text-[11px] text-[#FF7A18] font-bold flex items-center justify-between">
              <span>Configured: ₹{editForm.priceInr || 0} per {editForm.unit}</span>
              {editPricingType === "weight_based" && (
                <span className="text-[#8A8A8A] font-normal">Min: {editForm.minQty}{editForm.unit} (Step: {editForm.stepQty}{editForm.unit})</span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-[#171717] mb-1">
                Stock Quantity Counter
              </label>
              <input
                type="number"
                min="0"
                value={editForm.quantity}
                onChange={(e) => setEditForm({ ...editForm, quantity: e.target.value })}
                className="w-full bg-[#FFF9F2] border border-[#F0DED0] rounded-xl px-3 py-2 text-xs text-[#171717] font-mono outline-none focus:border-[#FF203D] font-bold"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-[#171717] mb-1">
                Description / Notes
              </label>
              <input
                type="text"
                placeholder="Crispy snack, hot beverage, etc."
                value={editForm.description}
                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                className="w-full bg-[#FFF9F2] border border-[#F0DED0] rounded-xl px-3 py-2 text-xs text-[#171717] outline-none focus:border-[#FF203D]"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#F0DED0]">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsEditModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" isLoading={isUpdatingProduct}>
              Save Changes
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
