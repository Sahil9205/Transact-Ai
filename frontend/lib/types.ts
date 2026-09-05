export type ProviderType = "local_merchant" | "marketplace" | "enterprise";
export type PricingType = "fixed_unit" | "weight_based" | "volume_based";
export type AvailabilityStatus = "in_stock" | "out_of_stock" | "limited";
export type FulfillmentType = "pickup" | "delivery";

export interface Merchant {
  provider_id: string;
  name: string;
  type: ProviderType;
  description?: string | null;
  location?: string | null;
  pincode?: string | null;
  api_key?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  business_type?: string | null;
  onboarding_status?: string;
  operational_status?: "open" | "paused" | "closed";
  is_active?: boolean;
}

export interface ProductPricing {
  amount: number; // in paise
  currency: string;
  pricing_type: PricingType;
  unit: string; // kg, piece, liter, etc.
  min_quantity?: number;
  increment_step?: number;
}

export interface ProductAvailability {
  status: AvailabilityStatus;
  quantity: number;
}

export interface Product {
  product_id: string;
  merchant_id: string;
  name: string;
  description?: string | null;
  category: string;
  price_amount: number;
  price_inr?: string;
  pricing_type?: PricingType;
  unit?: string;
  min_quantity?: number;
  increment_step?: number;
  quantity?: number;
  availability_status: AvailabilityStatus;
  fulfillment_type: FulfillmentType;
  prep_time_minutes?: number;
  pincode?: string | null;
}

export type OrderStatus =
  | "discovered"
  | "intent_parsed"
  | "merchant_verified"
  | "policy_validated"
  | "order_created"
  | "payment_pending"
  | "payment_success"
  | "ready_for_pickup"
  | "completed"
  | "cancelled"
  | "failed";

export interface Order {
  order_id: string;
  user_id: string;
  merchant_id: string;
  product_id: string;
  quantity: number;
  total_amount: number; // in paise
  total_amount_inr?: number;
  currency: string;
  status: OrderStatus;
  pincode?: string | null;
  delivery_address?: string | null;
  platform?: string | null;
  created_at?: string;
}

export interface SpendingPolicy {
  policy_id?: string;
  user_id: string;
  max_per_transaction_paise: number;
  max_per_transaction_inr: number;
  daily_limit_paise: number;
  daily_limit_inr: number;
  allowed_categories?: string[];
  is_active: boolean;
}

export interface User {
  user_id: string;
  name: string;
  email: string;
  phone?: string;
  address?: string;
  pincode?: string;
}

export interface DashboardStats {
  merchant: Merchant;
  total_products: number;
  total_orders: number;
  total_revenue_inr: number;
  platform_breakdown: Record<string, number>;
  recent_orders: Order[];
  products: Product[];
}
