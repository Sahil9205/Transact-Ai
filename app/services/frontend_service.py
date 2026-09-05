from __future__ import annotations
from pathlib import Path
import json
from typing import Any

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


class FrontendService:
    """Service to load and render frontend HTML templates from frontend/ directory."""

    @staticmethod
    def render_landing_page(all_merchants: list[dict[str, Any]]) -> str:
        template_path = FRONTEND_DIR / "landing.html"
        template = template_path.read_text(encoding="utf-8")

        switcher_options = ""
        for m in all_merchants:
            m_id = m.get("provider_id", "")
            m_name = m.get("name", "")
            switcher_options += f'<option value="{m_id}">{m_name}</option>\n'

        if not switcher_options:
            switcher_options = '<option value="">No registered stores yet</option>'

        return template.replace("__SWITCHER_OPTIONS__", switcher_options)

    @staticmethod
    def render_register_page() -> str:
        template_path = FRONTEND_DIR / "register.html"
        return template_path.read_text(encoding="utf-8")

    @staticmethod
    def render_dashboard_page(
        merchant_data: dict[str, Any],
        stats: dict[str, Any],
        all_merchants: list[dict[str, Any]],
    ) -> str:
        template_path = FRONTEND_DIR / "dashboard.html"
        template = template_path.read_text(encoding="utf-8")

        merchant_id = merchant_data.get("provider_id", "")
        merchant_name = merchant_data.get("name", "Store")
        merchant_pincode = merchant_data.get("pincode", "N/A") or "N/A"
        merchant_location = merchant_data.get("location", "") or "Delhi NCR"
        merchant_type = (merchant_data.get("type") or "local_merchant").replace("_", " ")
        api_key = merchant_data.get("api_key") or f"sk_live_{merchant_id[:16]}"

        total_products = stats.get("total_products", 0)
        total_orders = stats.get("total_orders", 0)
        total_revenue_inr = stats.get("total_revenue_inr", 0.0)
        recent_orders = stats.get("recent_orders", [])
        platforms = stats.get("platform_breakdown", {})

        switcher_options = ""
        for m in all_merchants:
            m_id = m.get("provider_id", "")
            m_name = m.get("name", "")
            selected = "selected" if m_id == merchant_id else ""
            switcher_options += f'<option value="{m_id}" {selected}>{m_name}</option>\n'

        platform_labels = json.dumps(list(platforms.keys()) if platforms else ["Claude", "ChatGPT", "Gemini", "Web"])
        platform_values = json.dumps(list(platforms.values()) if platforms else [4, 3, 2, 1])

        orders_rows = ""
        if not recent_orders:
            orders_rows = '<tr><td colspan="5" class="px-6 py-12 text-center text-xs font-medium text-[#5F5F5F]">No incoming orders yet. New customer orders placed via AI assistants will appear here in real-time.</td></tr>'
        else:
            for ord in recent_orders:
                o_id = getattr(ord, "order_id", ord.get("order_id", ""))
                raw_amt = getattr(ord, "total_amount", ord.get("total_amount", 0))
                o_amt = raw_amt / 100
                o_status = getattr(ord, "status", ord.get("status", "pending"))
                o_address = getattr(ord, "delivery_address", ord.get("delivery_address", "N/A")) or "N/A"
                o_pincode = getattr(ord, "pincode", ord.get("pincode", "N/A")) or "N/A"

                status_badge = "bg-[#FFF4E6] text-[#FF7A18] border-[#F0DED0]"
                status_label = str(o_status).replace('_', ' ')
                action_btn = f"""<button onclick="updateOrderStatus('{o_id}', 'ready_for_pickup')" class="px-3 py-1.5 bg-[#FFE8C7] hover:bg-[#FFD9A8] text-[#FF7A18] border border-[#FFD9A8] rounded-xl font-bold text-xs transition-colors cursor-pointer">Mark Ready</button>"""

                if o_status in ["completed", "order_created"]:
                    status_badge = "bg-emerald-50 text-emerald-700 border-emerald-200"
                    status_label = "Completed"
                    action_btn = """<span class="text-xs text-emerald-600 font-bold flex items-center justify-end gap-1"><span>✓</span> Fulfilled</span>"""
                elif o_status == "ready_for_pickup":
                    status_badge = "bg-[#FFE8C7] text-[#FF7A18] border-[#FFD9A8]"
                    status_label = "Ready for Pickup"
                    action_btn = f"""<button onclick="updateOrderStatus('{o_id}', 'completed')" class="px-3 py-1.5 bg-[#FF203D] hover:bg-[#E71937] text-white rounded-xl font-bold text-xs shadow-xs transition-colors cursor-pointer">Hand to Rider</button>"""

                orders_rows += f"""
                <tr class="hover:bg-[#FFF4E6]/60 border-b border-[#F0DED0] transition-colors">
                  <td class="px-5 py-4 text-xs font-mono font-bold text-[#171717]">#{o_id[:8].upper()}</td>
                  <td class="px-5 py-4 text-xs text-[#5F5F5F] max-w-xs truncate" title="{o_address}">
                    <span class="font-bold text-[#171717]">PIN: {o_pincode}</span> &middot; {o_address}
                  </td>
                  <td class="px-5 py-4 text-xs font-bold text-[#171717] font-mono-num">₹{o_amt:.2f}</td>
                  <td class="px-5 py-4 text-xs">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border {status_badge} capitalize">
                      {status_label}
                    </span>
                  </td>
                  <td class="px-5 py-4 text-xs text-right">
                    {action_btn}
                  </td>
                </tr>
                """

        operational_status = str(merchant_data.get("operational_status") or "open")
        products_json = json.dumps(stats.get("products", []))
        orders_json = json.dumps([
            {
                "order_id": getattr(o, "order_id", o.get("order_id", "") if isinstance(o, dict) else ""),
                "total_amount": getattr(o, "total_amount", o.get("total_amount", 0) if isinstance(o, dict) else 0),
                "status": getattr(o, "status", o.get("status", "pending") if isinstance(o, dict) else "pending"),
                "platform": getattr(o, "platform", o.get("platform", "unknown") if isinstance(o, dict) else "unknown") or "unknown",
                "delivery_address": getattr(o, "delivery_address", o.get("delivery_address", "N/A") if isinstance(o, dict) else "N/A") or "N/A",
                "pincode": getattr(o, "pincode", o.get("pincode", "N/A") if isinstance(o, dict) else "N/A") or "N/A",
            }
            for o in recent_orders
        ])

        return (
            template
            .replace("__MERCHANT_NAME__", merchant_name)
            .replace("__MERCHANT_ID__", merchant_id)
            .replace("__MERCHANT_PINCODE__", merchant_pincode)
            .replace("__MERCHANT_LOCATION__", merchant_location)
            .replace("__MERCHANT_TYPE__", merchant_type)
            .replace("__API_KEY__", api_key)
            .replace("__TOTAL_REVENUE__", f"{total_revenue_inr:.2f}")
            .replace("__TOTAL_ORDERS__", str(total_orders))
            .replace("__TOTAL_PRODUCTS__", str(total_products))
            .replace("__SWITCHER_OPTIONS__", switcher_options)
            .replace("__ORDERS_ROWS__", orders_rows)
            .replace("__PLATFORM_LABELS__", platform_labels)
            .replace("__PLATFORM_VALUES__", platform_values)
            .replace("__OPERATIONAL_STATUS__", operational_status)
            .replace("__PRODUCTS_DATA_JSON__", products_json)
            .replace("__ORDERS_DATA_JSON__", orders_json)
        )

    @staticmethod
    def render_checkout_page(
        order: Any,
        product: Any,
        merchant: Any,
        payment: Any,
        cfg: Any,
    ) -> str:
        template_path = FRONTEND_DIR / "checkout.html"
        template = template_path.read_text(encoding="utf-8")

        order_id = order.order_id
        product_name = product.name if product else "Groceries"
        merchant_name = merchant.name if merchant else "Quick Commerce Hub"
        amount_inr = f"{order.total_amount / 100:.2f}"
        amount_paise = order.total_amount
        razorpay_order_id = payment.provider_ref if payment else f"order_{order.order_id[:14]}"
        key_id = cfg.RAZORPAY_KEY_ID
        is_paid = order.status in ("payment_success", "confirmed", "order_created", "completed")
        prep_time = getattr(product, "prep_time_minutes", 10) or 10
        pincode = order.pincode or getattr(product, "pincode", None) or getattr(merchant, "pincode", None) or "N/A"
        delivery_address = order.delivery_address or ""
        platform_name = (order.platform or "AI Agent").capitalize()

        if is_paid:
            payment_card = f"""
            <div class="success-box">
                <div class="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xl mx-auto mb-3">✓</div>
                <div class="success-title">Order Already Paid</div>
                <p style="color:#5F5F5F;font-size:14px;">Your delivery of <strong>{product_name}</strong> is in transit ({prep_time} min delivery).</p>
            </div>
            """
        else:
            addr_row = f'<div class="row"><span class="label">Address</span><span class="value" style="font-size:12px;max-width:200px;text-align:right;color:#171717;">{delivery_address}</span></div>' if delivery_address else ""
            payment_card = f"""
            <div class="badge">Razorpay Secure 256-Bit Checkout</div>
            <h1>{product_name}</h1>
            <div class="merchant">Sold by <strong>{merchant_name}</strong> • {prep_time} min delivery</div>
            
            <div class="details-box">
                <div class="row"><span class="label">Quantity</span><span class="value">{order.quantity} unit</span></div>
                <div class="row"><span class="label">Ordered Via</span><span class="value" style="color:#FF7A18;font-weight:700;">{platform_name}</span></div>
                <div class="row"><span class="label">Destination</span><span class="value">Pincode {pincode}</span></div>
                {addr_row}
                <div class="row"><span class="label">Order ID</span><span class="value" style="font-family:monospace;font-size:12px;">{order_id[:8]}...{order_id[-4:]}</span></div>
                <div class="row"><span class="label">Total Amount</span><span class="value price">₹{amount_inr}</span></div>
            </div>

            <button class="btn" onclick="payNow()">
                Pay ₹{amount_inr} via Razorpay
            </button>

            <button class="btn btn-test" onclick="simulateTestPayment()">
                Simulate Instant Test Payment (Mock Success)
            </button>

            <div class="footer">
                Powered by TransactAI • Razorpay Secure
            </div>
            """

        return (
            template
            .replace("__AMOUNT_INR__", amount_inr)
            .replace("__KEY_ID__", key_id)
            .replace("__AMOUNT_PAISE__", str(amount_paise))
            .replace("__PRODUCT_NAME__", product_name)
            .replace("__RAZORPAY_ORDER_ID__", razorpay_order_id)
            .replace("__PREP_TIME__", str(prep_time))
            .replace("__PAYMENT_CARD_CONTENT__", payment_card)
        )
