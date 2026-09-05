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
  AlertCircle
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

  // Modal State
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

  // Load Data
  const fetchData = useCallback(async () => {
    if (!merchantId) return;
    try {
      setLoading(true);
      const [statsData, ordersData] = await Promise.all([
        api.getDashboardStats(merchantId).catch(() => null),
        api.listMerchantOrders(merchantId).catch(() => []),
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
                <span className="text-[#E8CDBB]">&bull;</span>
                <Link
                  href="/merchant"
                  className="text-[#FF7A18] hover:text-[#FF203D] font-bold transition-colors inline-flex items-center gap-1"
                >
                  Switch Store <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </div>
          </div>

          {/* Operational Header Actions */}
          <div className="flex items-center gap-3 shrink-0">
            {/* Store Status Toggle (Open ↔ Paused) */}
            <button
              onClick={toggleStoreStatus}
              disabled={isUpdatingStatus}
              className={cn(
                "h-10 inline-flex items-center gap-2 px-4 rounded-xl text-xs font-bold transition-all border shadow-xs cursor-pointer whitespace-nowrap",
                isStoreOpen
                  ? "bg-emerald-50 border-emerald-300 text-emerald-800 hover:bg-emerald-100"
                  : "bg-amber-50 border-amber-300 text-amber-900 hover:bg-amber-100"
              )}
            >
              <span className="relative flex h-2.5 w-2.5 shrink-0">
                <span
                  className={cn(
                    "animate-ping absolute inline-flex h-full w-full rounded-full opacity-75",
                    isStoreOpen ? "bg-emerald-400" : "bg-amber-400"
                  )}
                />
                <span
                  className={cn(
                    "relative inline-flex rounded-full h-2.5 w-2.5",
                    isStoreOpen ? "bg-emerald-500" : "bg-amber-500"
                  )}
                />
              </span>
              <span>{isStoreOpen ? "Accepting Orders" : "Store Paused"}</span>
            </button>

            {/* Primary Add Item CTA */}
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="h-10 inline-flex items-center gap-2 px-4 sm:px-5 rounded-xl bg-[#FF203D] hover:bg-[#E71937] text-white text-xs font-extrabold transition-all shadow-sm cursor-pointer active:scale-95 whitespace-nowrap"
            >
              <Plus className="w-4 h-4" />
              <span>Add Menu Item</span>
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
                    <th className="px-5 py-3.5">Destination</th>
                    <th className="px-5 py-3.5">Amount</th>
                    <th className="px-5 py-3.5">Status</th>
                    <th className="px-5 py-3.5 text-right">Fulfillment</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F0DED0] text-xs">
                  {filteredOrders.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-5 py-12 text-center text-[#5F5F5F]">
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

                      return (
                        <tr
                          key={order.order_id}
                          className="hover:bg-[#FFF9F2]/60 transition-colors"
                        >
                          <td className="px-5 py-4 font-mono font-bold text-[#171717]">
                            #{order.order_id.slice(0, 8)}
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
                    <th className="px-4 py-3">Item / Category</th>
                    <th className="px-4 py-3">Price</th>
                    <th className="px-4 py-3 text-center">Stock</th>
                    <th className="px-4 py-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F0DED0] text-xs">
                  {filteredCatalog.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-4 py-10 text-center text-[#5F5F5F]">
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
                          <td className="px-4 py-3.5">
                            <div className="font-bold text-xs text-[#171717]">{item.name}</div>
                            <div className="text-[10px] text-[#5F5F5F] uppercase tracking-wider font-semibold">
                              {item.category || "General"}
                            </div>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className="font-mono font-bold text-xs text-[#171717]">
                              ₹{price} / {unit}
                            </span>
                            {isWeight && (
                              <div className="text-[10px] text-[#FF7A18] font-mono">
                                Min: {item.min_quantity || 0.25}
                                {unit}
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-3.5 text-center">
                            <div className="inline-flex items-center gap-1.5 bg-[#FFF9F2] border border-[#F0DED0] px-2 py-1 rounded-lg font-mono text-xs">
                              <button
                                onClick={() => handleAdjustQuantity(item.product_id, -1)}
                                className="text-[#5F5F5F] hover:text-[#171717] px-1 font-bold cursor-pointer"
                              >
                                &minus;
                              </button>
                              <span className="text-[#171717] font-bold w-5 text-center">
                                {item.quantity ?? 0}
                              </span>
                              <button
                                onClick={() => handleAdjustQuantity(item.product_id, 1)}
                                className="text-[#5F5F5F] hover:text-[#171717] px-1 font-bold cursor-pointer"
                              >
                                &plus;
                              </button>
                            </div>
                          </td>
                          <td className="px-4 py-3.5 text-right">
                            <button
                              onClick={() =>
                                handleToggleProductAvailability(
                                  item.product_id,
                                  item.availability_status
                                )
                              }
                              className={cn(
                                "px-2.5 py-1 rounded-lg text-[11px] font-bold transition-colors cursor-pointer border shadow-2xs whitespace-nowrap",
                                inStock
                                  ? "bg-emerald-50 text-emerald-700 border-emerald-300 hover:bg-emerald-100"
                                  : "bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100"
                              )}
                            >
                              {inStock ? "● In Stock" : "○ Out of Stock"}
                            </button>
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
    </div>
  );
}
