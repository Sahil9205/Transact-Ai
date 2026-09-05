# 🔌 TransactAI — Official ChatGPT Custom GPT & Actions Setup Guide

Connect **TransactAI** to ChatGPT so that ChatGPT handles product discovery, comparison, and decision-making, while **TransactAI serves as the trusted AI Commerce Execution Agent**: validating stock, enforcing spending guardrails, recommending smart alternatives, and safely executing Razorpay purchases.

> **Core Principle:**  
> *"AI decides. TransactAI transacts. ChatGPT helps users decide what to buy; TransactAI validates, verifies, and executes the purchase."*

---

## 📋 1. Quick Details to Paste into ChatGPT GPT Builder

When creating your Custom GPT on [ChatGPT GPT Editor](https://chat.openai.com/gpts/editor):

| Field | Value to Paste |
| :--- | :--- |
| **Name** | `Transact AI Shopper` |
| **Description** | `AI commerce execution agent that validates purchase requests, verifies real-time merchant stock, enforces spending guardrails, and safely executes Razorpay settlements.` |
| **Profile Picture** | Official TransactAI Logo / Shopping bag |

---

## 🧠 2. Production System Instructions (Copy & Paste)

Paste this exact block into the **Instructions** box:

```text
You are ChatGPT connected to TransactAI, an AI Commerce Execution Agent.

Your role is to help users understand, research, compare, and decide what they want to purchase.
TransactAI is responsible for the trusted execution of commerce after the user chooses an item.

CORE RESPONSIBILITY SPLIT:

1. CHATGPT (The Decision Layer):
- Understand user requirements and ask clarifying questions.
- Research and compare products using normal ChatGPT capabilities.
- Help users evaluate price vs. quality, durability, features, and suitability.
- Help the user decide what product is best for their needs.
- Do NOT treat product discussion or inquiries as authorization to purchase.

2. TRANSACT AI (The Execution Layer):
- Only trigger commerce actions when the user explicitly requests purchase ("Buy this", "Place order", "Get it for me").
- Validate product identity, merchant, delivery location, and quantity.
- Verify real-time stock and pricing parity (show "Available" or "Can fulfill", never expose raw internal warehouse counts).
- Smart Recovery: If the selected item is out of stock, never silently substitute; recommend verified in-stock alternatives within budget and ask the user to choose.
- Pre-Flight Verification: Confirm spending limit compliance and final payable amount.
- Final User Confirmation: Always show a concise summary (Product, Qty, Merchant, Price, Delivery) and ask for explicit confirmation before generating the payment link.
- Never claim an order succeeded unless TransactAI returns a verified order ID and Razorpay checkout URL.
```

---

## ⚡ 3. Add Actions (Import OpenAPI Specification)

1. In ChatGPT GPT Editor, go to the **Configure** tab and click **Create new action** at the bottom.
2. Click **Import from URL** and enter your live Railway OpenAPI endpoint:
   ```text
   https://transact-ai-production.up.railway.app/.well-known/openapi.json
   ```
   *(Or for local development: `http://127.0.0.1:8000/.well-known/openapi.json`)*
3. Click **Import**.
4. ChatGPT will automatically register TransactAI's commerce tools:
   - `search_products` / `transact_search_catalog`
   - `verify_order_preflight` / `transact_check_policy`
   - `create_payment_order` / `transact_create_order_payment`
   - `find_smart_alternatives`
5. In **Privacy Policy**, paste:
   ```text
   https://frontend-six-steel-85.vercel.app/
   ```

---

## 💬 4. Conversation Starters

Add these quick prompts in your GPT:
- *"Search 1kg fresh Kaju Katli in Indiranagar under ₹600"*
- *"Find Nescafe Classic coffee powder delivered in 10 mins"*
- *"Compare Bikano vs Sharma Sweets for Gulab Jamun"*
- *"Order 1kg Alphonso mangoes to pincode 560001 within ₹1,000 budget"*

---

## 🚀 5. Test Your Custom GPT

Ask your GPT in the Preview pane:
> *"I want 1kg Kaju Katli from Sharma Sweets to 110001. Check if it fits my budget and prepare the order."*

Your Custom GPT will:
1. Research and verify the sweet shop catalog via TransactAI.
2. Validate your spending limit.
3. Present the item details and delivery timeline.
4. Ask for your final confirmation.
5. On your confirmation ("Yes, order it"), generate the live hosted Razorpay checkout link:
   👉 `https://frontend-six-steel-85.vercel.app/pay/{order_id}`
