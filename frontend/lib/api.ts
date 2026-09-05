import { DashboardStats, Merchant, Order, Product, SpendingPolicy } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!res.ok) {
    let errorDetails = "";
    try {
      const json = await res.json();
      errorDetails = json.message || JSON.stringify(json);
    } catch {
      errorDetails = res.statusText;
    }
    throw new Error(`API error ${res.status}: ${errorDetails}`);
  }

  return res.json() as Promise<T>;
}

export const api = {
  // Merchant API
  async listMerchants(): Promise<Merchant[]> {
    return apiFetch<Merchant[]>("/api/v1/merchants/");
  },

  async getMerchant(merchantId: string): Promise<Merchant> {
    return apiFetch<Merchant>(`/api/v1/merchants/${merchantId}`);
  },

  async registerMerchant(payload: {
    name: string;
    type: string;
    description?: string;
    location?: string;
    pincode?: string;
    contact_phone?: string;
    contact_email?: string;
    business_type?: string;
  }): Promise<Merchant> {
    return apiFetch<Merchant>("/api/v1/merchants/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getDashboardStats(merchantId: string): Promise<DashboardStats> {
    return apiFetch<DashboardStats>(`/api/v1/merchants/${merchantId}/dashboard-stats`);
  },

  async updateOperationalStatus(
    merchantId: string,
    operationalStatus: "open" | "paused" | "closed"
  ): Promise<Merchant> {
    return apiFetch<Merchant>(`/api/v1/merchants/${merchantId}/status`, {
      method: "POST",
      body: JSON.stringify({ operational_status: operationalStatus }),
    });
  },

  async addProduct(merchantId: string, product: Record<string, any>): Promise<any> {
    return apiFetch<any>(`/merchants/${merchantId}/products`, {
      method: "POST",
      body: JSON.stringify(product),
    });
  },

  async toggleProductAvailability(
    merchantId: string,
    productId: string,
    status: "in_stock" | "out_of_stock" | "limited"
  ): Promise<any> {
    return apiFetch<any>(`/api/v1/merchants/${merchantId}/products/${productId}/availability`, {
      method: "POST",
      body: JSON.stringify({ availability_status: status }),
    });
  },

  async adjustProductQuantity(productId: string, quantity: number): Promise<any> {
    return apiFetch<any>(`/api/v1/products/${productId}`, {
      method: "PATCH",
      body: JSON.stringify({ quantity }),
    });
  },

  // Order API
  async getOrder(orderId: string): Promise<Order> {
    return apiFetch<Order>(`/api/v1/orders/${orderId}`);
  },

  async listUserOrders(userId: string): Promise<Order[]> {
    return apiFetch<Order[]>(`/api/v1/orders/users/${userId}`);
  },

  async listMerchantOrders(merchantId: string, statusFilter?: string): Promise<Order[]> {
    const query = statusFilter && statusFilter !== "all" ? `?status_filter=${statusFilter}` : "";
    return apiFetch<Order[]>(`/api/v1/orders/merchants/${merchantId}${query}`);
  },

  async updateOrderStatus(orderId: string, status: string, merchantId?: string): Promise<any> {
    return apiFetch<any>(`/api/v1/orders/${orderId}/status`, {
      method: "POST",
      body: JSON.stringify({ status, merchant_id: merchantId || "" }),
    });
  },

  // Payment API
  async verifyPayment(payload: {
    razorpay_order_id: string;
    razorpay_payment_id: string;
    razorpay_signature: string;
  }): Promise<any> {
    return apiFetch<any>("/api/v1/payments/verify-signature", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // Policy API
  async getUserPolicy(userId: string): Promise<{
    policy: SpendingPolicy | null;
    spent_today_inr: number;
    remaining_daily_budget_inr: number | null;
  }> {
    return apiFetch<any>(`/api/v1/policies/users/${userId}`);
  },

  async configureUserPolicy(
    userId: string,
    payload: {
      max_per_transaction_inr: number;
      daily_limit_inr: number;
      allowed_categories?: string[];
      is_active?: boolean;
    }
  ): Promise<SpendingPolicy> {
    return apiFetch<SpendingPolicy>(`/api/v1/policies/users/${userId}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};

