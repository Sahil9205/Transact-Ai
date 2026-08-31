# 🔵 Transact AI — Official Google Gemini & Gemini Gems Integration Guide

Connect Transact AI to **Google Gemini** and **Gemini Gems** in 2 minutes.

---

## ⚡ Method 1: Gemini Gems (Gemini Advanced / Web UI)

Google Gemini allows creating custom **Gems** (similar to Custom GPTs).

### Step 1: Create a New Gem
1. Go to [gemini.google.com](https://gemini.google.com) $\rightarrow$ Click **Gems Manager** $\rightarrow$ **+ New Gem**.
2. **Name**: `Transact AI Shopper`
3. **Instructions** (Paste this block):
```text
You are Transact AI, an intelligent autonomous commerce assistant capable of searching, comparing, and purchasing products across local shops (Sharma Sweets), quick-commerce dark stores (Blinkit, Zepto), and e-commerce marketplaces (Amazon).

OPERATIONAL WORKFLOW:
1. When a user asks to buy any product (sweets, groceries, coffee, medicines), query the Transact AI catalog.
2. Present the top matches with Prices (₹ INR), Merchant Name, Platform Type, and Delivery SLA.
3. When the user confirms an option, ask for their delivery address.
4. Verify warehouse stock and spending policy before payment.
5. Provide the secure Razorpay payment link:
   👉 [Pay ₹{amount} via UPI / Card]({payment_link_url})
```

---

## ⚡ Method 2: Google AI Studio / Gemini API (Function Calling Extension)

If you are using **Google AI Studio** ([aistudio.google.com](https://aistudio.google.com)) or the Gemini Python SDK (`google-generativeai`):

### 1. In Google AI Studio UI:
1. Open Google AI Studio $\rightarrow$ Create a **Chat Prompt** (`gemini-1.5-pro` or `gemini-1.5-flash`).
2. In the right sidebar, enable **Function Calling / Tools**.
3. Click **Add Tool** $\rightarrow$ Paste the tool schema from:
   `http://127.0.0.1:8000/api/v1/hosts/tools?format=gemini`
   *(Or import `/.well-known/gemini-extension.json`)*

### 2. In Python with `google-generativeai`:
```python
import google.generativeai as genai
import httpx

# 1. Fetch Gemini tool declarations from Transact AI
with httpx.Client() as client:
    res = client.get("http://127.0.0.1:8000/api/v1/hosts/tools?format=gemini")
    gemini_tools = res.json()

# 2. Configure Gemini Model with Transact AI Tools
genai.configure(api_key="YOUR_GEMINI_API_KEY")
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools=gemini_tools,
)

# 3. Chat with Gemini
chat = model.start_chat(enable_automatic_function_calling=False)
response = chat.send_message("1kg Rasgulla under 500 in 110001")
print(response.candidates[0].content.parts)
```

---

## 💬 Conversation Starters for Gemini

- *"Find 1kg Rasgulla in CP under ₹500"*
- *"Nescafe coffee powder for cold coffee in CP"*
- *"Compare Bikano Rasgulla vs Sharma Sweets"*
- *"Order Crocin Advance from Apollo Pharmacy"*
