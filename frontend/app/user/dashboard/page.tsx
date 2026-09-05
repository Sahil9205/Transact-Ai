"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ShieldCheck,
  ShoppingBag,
  Sliders,
  RefreshCw,
  Clock,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  ExternalLink,
  ChevronRight,
  TrendingUp,
  User as UserIcon,
} from "lucide-react";
import { api } from "@/lib/api";
import { Order, SpendingPolicy } from "@/lib/types";
import { formatINR, cn } from "@/lib/utils";
import { useToast } from "@/components/ui/Toast";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import PatternDivider from "@/components/patterns/PatternDivider";

export default function UserDashboardPage() {
  const router = useRouter();
  const { showToast } = useToast();

  const [userId, setUserId] = useState<string>("buyer-1");
  const [loading, setLoading] = useState(true);
  const [policyData, setPolicyData] = useState<{
    policy: SpendingPolicy | null;
    spent_today_inr: number;
    remaining_daily_budget_inr: number | null;
  } | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);

  // Load User Data
  const loadUserData = useCallback(async (currentUserId: string) => {
    try {
      setLoading(true);
      const [policyRes, ordersRes] = await Promise.all([
        api.getUserPolicy(currentUserId).catch(() => null),
        api.listUserOrders(currentUserId).catch(() => []),
      ]);

      if (policyRes) {
        setPolicyData(policyRes);
      } else {
        // Fallback default mock telemetry if fresh buyer
        setPolicyData({
          policy: {
            user_id: currentUserId,
            max_per_transaction_inr: 1000,
            max_per_transaction_paise: 100000,
            daily_limit_inr: 3000,
            daily_limit_paise: 300000,
            is_active: true,
            allowed_categories: ["food", "sweets", "groceries"],
          },
          spent_today_inr: 0,
          remaining_daily_budget_inr: 3000,
        });
      }

      setOrders(ordersRes || []);
    } catch (err) {
      console.error("User data fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const activeUser = localStorage.getItem("transactai_active_user_id") || "buyer-1";
    setUserId(activeUser);
    loadUserData(activeUser);
  }, [loadUserData]);

  const spentToday = policyData?.spent_today_inr ?? 0;
  const dailyLimit = policyData?.policy?.daily_limit_inr ?? 3000;
  const maxPerTx = policyData?.policy?.max_per_transaction_inr ?? 1000;
  const percentSpent = Math.min(100, Math.round((spentToday / (dailyLimit || 1)) * 100));

  return (
    <div className="min-h-screen bg-[#FFF9F2] text-[#171717] pb-16">
      {/* Top Header */}
      <header className="bg-white/95 backdrop-blur-md border-b border-[#F0DED0] sticky top-0 z-30 shadow-[0_2px_12px_rgba(240,222,208,0.45)]">
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 min-h-[76px] py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-11 h-11 rounded-2xl bg-[#FFF4E6] border border-[#FFD9A8] flex items-center justify-center text-[#FF203D] shrink-0 shadow-inner">
              <UserIcon className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-extrabold text-xl sm:text-2xl text-[#171717] tracking-tight">
                Buyer Control Console
              </h1>
              <div className="text-xs text-[#5F5F5F] flex items-center gap-2 mt-0.5">
                <span>
                  Active Buyer: <strong className="text-[#171717] font-mono">{userId}</strong>
                </span>
                <span className="text-[#E8CDBB]">&bull;</span>
                <Link
                  href="/user/login"
                  className="text-[#FF7A18] hover:text-[#FF203D] font-bold transition-colors"
                >
                  Switch User &rarr;
                </Link>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link href="/user/onboarding">
              <Button variant="outline" size="sm" className="hidden sm:inline-flex text-xs">
                <Sliders className="w-3.5 h-3.5 mr-1" />
                <span>Adjust Limits</span>
              </Button>
            </Link>

            <button
              onClick={() => loadUserData(userId)}
              title="Refresh State"
              className="w-9 h-9 rounded-xl bg-[#FFF4E6] hover:bg-[#FFE8C7] border border-[#F0DED0] text-[#5F5F5F] hover:text-[#171717] flex items-center justify-center transition-colors cursor-pointer"
            >
              <RefreshCw className={cn("w-4 h-4", loading && "animate-spin text-[#FF7A18]")} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Telemetry Cards */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Daily Budget Tracker */}
          <div className="bg-white rounded-3xl p-6 border border-[#F0DED0] shadow-sm relative overflow-hidden group hover:border-[#FFD9A8] transition-all">
            <div className="flex items-center justify-between text-[#5F5F5F] text-xs font-bold">
              <span>Today&apos;s Spending Cap</span>
              <span className="text-emerald-700 font-mono text-[11px] bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full font-bold">
                {percentSpent}% Used
              </span>
            </div>

            <div className="mt-4">
              <div className="text-3xl font-black text-[#171717] font-mono tracking-tight">
                {formatINR(spentToday)}
                <span className="text-sm font-medium text-[#8A8A8A] ml-2">
                  / {formatINR(dailyLimit)}
                </span>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-2.5 bg-[#FFF4E6] rounded-full mt-3 overflow-hidden border border-[#F0DED0]">
                <div
                  className="h-full bg-gradient-to-r from-[#FF7A18] to-[#FF203D] rounded-full transition-all duration-500"
                  style={{ width: `${percentSpent}%` }}
                />
              </div>

              <div className="text-xs text-[#5F5F5F] mt-2 flex justify-between">
                <span>Remaining: {formatINR(Math.max(0, dailyLimit - spentToday))}</span>
                <span>Resets at midnight</span>
              </div>
            </div>
          </div>

          {/* Max Per Transaction Limit */}
          <div className="bg-white rounded-3xl p-6 border border-[#F0DED0] shadow-sm relative overflow-hidden group hover:border-[#FFD9A8] transition-all">
            <div className="flex items-center justify-between text-[#5F5F5F] text-xs font-bold">
              <span>Max Single Transaction</span>
              <span className="text-[#171717] font-mono text-[11px] bg-[#FFF4E6] border border-[#F0DED0] px-2 py-0.5 rounded-full font-bold">
                Deterministic
              </span>
            </div>

            <div className="mt-4">
              <div className="text-3xl font-black text-[#171717] font-mono tracking-tight">
                {formatINR(maxPerTx)}
              </div>
              <div className="text-xs text-[#5F5F5F] mt-2">
                Agent orders exceeding this threshold are blocked instantly by the policy engine.
              </div>
            </div>
          </div>

          {/* Policy Guardrail Status */}
          <div className="bg-white rounded-3xl p-6 border border-[#F0DED0] shadow-sm relative overflow-hidden group hover:border-[#FFD9A8] transition-all flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-[#5F5F5F] text-xs font-bold">
                <span>Policy Enforcement</span>
                <span className="text-emerald-700 font-mono text-[11px] bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full font-bold">
                  Active
                </span>
              </div>
              <div className="mt-3 flex items-center gap-2">
                <ShieldCheck className="w-6 h-6 text-emerald-600" />
                <span className="text-sm font-extrabold text-[#171717]">
                  Zero Unauthorized Spend
                </span>
              </div>
              <p className="text-xs text-[#5F5F5F] mt-1.5">
                Every AI prompt triggers an atomic DB transaction with mathematical bounds checking.
              </p>
            </div>

            <div className="pt-3">
              <Link href="/user/onboarding">
                <span className="text-xs font-bold text-[#FF7A18] hover:text-[#FF203D] inline-flex items-center gap-1 transition-colors">
                  Edit Spending Guardrails &rarr;
                </span>
              </Link>
            </div>
          </div>
        </section>

        {/* Chronological Agent Orders */}
        <section className="bg-white rounded-3xl border border-[#F0DED0] overflow-hidden shadow-sm">
          <div className="p-6 border-b border-[#F0DED0] flex items-center justify-between">
            <div>
              <h2 className="text-lg font-extrabold text-[#171717] flex items-center gap-2">
                <span>Autonomous Orders History</span>
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              </h2>
              <p className="text-xs text-[#5F5F5F] mt-1">
                Purchases executed or initiated by AI agents on your behalf
              </p>
            </div>

            <Link href="/pay">
              <span className="text-xs font-bold text-[#FF7A18] hover:text-[#FF203D] transition-colors">
                Pending Payments
              </span>
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#FFF9F2] border-b border-[#F0DED0] text-[11px] uppercase tracking-wider text-[#5F5F5F] font-bold">
                  <th className="px-5 py-3.5 font-mono">Order Reference</th>
                  <th className="px-5 py-3.5">Destination</th>
                  <th className="px-5 py-3.5">Total Amount</th>
                  <th className="px-5 py-3.5">Fulfillment Status</th>
                  <th className="px-5 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F0DED0] text-xs">
                {orders.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-5 py-12 text-center text-[#5F5F5F]">
                      <ShoppingBag className="w-8 h-8 text-[#FFD9A8] mx-auto mb-2 opacity-60" />
                      <p className="font-bold text-sm text-[#171717]">No agent orders recorded</p>
                      <p className="text-xs text-[#8A8A8A] mt-1">
                        When an AI assistant creates an order, it will immediately appear here.
                      </p>
                    </td>
                  </tr>
                ) : (
                  orders.map((order) => {
                    const isPendingPay = order.status === "payment_pending";
                    const isCompleted = order.status === "completed";

                    return (
                      <tr key={order.order_id} className="hover:bg-[#FFF9F2]/60 transition-colors">
                        <td className="px-5 py-4 font-mono font-bold text-[#171717]">
                          #{order.order_id.slice(0, 10)}
                        </td>
                        <td className="px-5 py-4">
                          <div className="font-semibold text-[#171717]">
                            {order.delivery_address || "Local Delivery"}
                          </div>
                          <div className="text-[10px] text-[#5F5F5F] font-mono mt-0.5">
                            PIN: {order.pincode || "—"}
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
                                : isPendingPay
                                ? "bg-amber-50 text-amber-800 border-amber-200"
                                : "bg-blue-50 text-blue-700 border-blue-200"
                            )}
                          >
                            {(order.status || "order_created").replace(/_/g, " ")}
                          </span>
                        </td>
                        <td className="px-5 py-4 text-right">
                          {isPendingPay ? (
                            <Link href={`/pay/${order.order_id}`}>
                              <button className="px-3 py-1.5 rounded-xl bg-[#FF203D] hover:bg-[#E71937] text-white font-bold text-xs transition-all cursor-pointer shadow-2xs">
                                Pay Now &rarr;
                              </button>
                            </Link>
                          ) : (
                            <span className="text-xs text-[#8A8A8A] font-semibold">
                              Settled ✓
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
        </section>
      </main>
    </div>
  );
}
