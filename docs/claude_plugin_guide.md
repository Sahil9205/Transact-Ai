# 🟣 Transact AI — Official Anthropic Claude Integration Guide

Connect Transact AI to **Anthropic Claude Desktop** and **Claude.ai Web/Mobile** in under 1 minute.

---

## ☁️ Option A: Remote Cloud Connector (Claude.ai Web, Mobile & Cowork)

Use this method to connect to your **Railway Deployed Server** without needing Python on your local machine:

### Step 1: Open Connectors in Claude.ai
1. Open [Claude.ai](https://claude.ai) in your browser or mobile app.
2. Go to **Customize** $\rightarrow$ **Connectors**.
3. Click the **"+"** button $\rightarrow$ **"Add custom connector"**.

### Step 2: Paste your Railway Remote MCP Endpoint
- **Connector Name**: `Transact AI`
- **Connector URL**:
  ```text
  https://transact-ai-production.up.railway.app/mcp
  ```
- Click **Add**.

### Step 3: Start Shopping!
In any Claude chat, enable the connector and ask:
> *"Search 1kg Rasgulla under ₹500 in 110001 across all connected stores"*

---

## 💻 Option B: Local Laptop (Claude Desktop App via stdio)

Use this method for offline local desktop development:

### Step 1: Open Configuration File
On Windows:
```text
%APPDATA%\Claude\claude_desktop_config.json
```

### Step 2: Paste the Local MCP Server Config
```json
{
  "mcpServers": {
    "transact-ai": {
      "command": "C:/Users/ASUS/Desktop/resume project/Razorpay/razorpay/python.exe",
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
2. You will see the **🔨 Hammer / Tools Icon** loaded with 5 Transact AI commerce tools!
