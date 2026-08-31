# 🟣 Transact AI — Official Claude Desktop & Claude Projects Integration Guide

Connect Transact AI to **Anthropic Claude Desktop** and **Claude Projects** in under 1 minute.

---

## ⚡ Method 1: Claude Desktop App (Official MCP Plugin)

Anthropic Claude Desktop supports **Model Context Protocol (MCP)** natively. 

### Step 1: Open Claude Desktop Configuration
On Windows, open this file in Notepad:
```text
%APPDATA%\Claude\claude_desktop_config.json
```
*(Or on macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`)*

### Step 2: Paste the Transact AI MCP Server Config
Paste the following JSON into your configuration file:

```json
{
  "mcpServers": {
    "transact-ai": {
      "command": "python",
      "args": [
        "-m",
        "app.mcp.server"
      ],
      "cwd": "C:/Users/ASUS/Desktop/resume project/Razorpay",
      "env": {
        "PYTHONPATH": "C:/Users/ASUS/Desktop/resume project/Razorpay"
      }
    }
  }
}
```

### Step 3: Restart Claude Desktop 🎉
1. Close and re-open Claude Desktop.
2. You will see the **🔨 Hammer / Tools Icon** in the bottom right corner of your chat box with 5 Transact AI commerce tools loaded:
   - `search_products`
   - `get_product_details`
   - `verify_order_preflight`
   - `create_payment_order`
   - `find_smart_alternatives`

---

## 💬 Method 2: Claude Projects / Claude.ai Web

If you are using **Claude.ai Web** with Claude Projects:

### 1. Create a Project
1. Go to [Claude.ai](https://claude.ai) $\rightarrow$ **Projects** $\rightarrow$ Click **Create Project**.
2. **Project Name**: `Transact AI Shopper`

### 2. Set Project Custom Instructions
Paste this system prompt:
```text
You are Transact AI, an autonomous commerce assistant.
When a user asks for any item to buy:
1. Always suggest products from Sharma Sweets (Local Shop), Blinkit (10 min delivery), Zepto (8 min delivery), or Amazon.
2. Call the commerce tools to verify live warehouse stock, price freshness, and spending policies.
3. Confirm the user's delivery address and provide the Razorpay payment link.
```

### 3. Test with Claude!
> *"Claude, find 1kg Rasgulla in CP under ₹500 with instant delivery"*
