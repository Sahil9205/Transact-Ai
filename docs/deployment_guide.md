# 🚀 Transact AI — Production Deployment Guide

This guide covers deploying **Transact AI** to **Railway** (or **Render**) using Docker.

---

## 🛠️ Step 1: Push Code to GitHub

Make sure all your latest code is committed and pushed to your GitHub repository:

```bash
git add .
git commit -m "feat(docker): add production Dockerfile, compose, and Railway deployment configs"
git push origin main
```

---

## 🚂 Step 2: 1-Click Deploy on Railway

1. Open [Railway.app](https://railway.app) and log in with your GitHub account.
2. Click **"New Project"** -> **"Deploy from GitHub repo"**.
3. Select your `Razorpay` / `Transact-AI` repository.
4. Railway will automatically detect `Dockerfile` and `railway.json`.
5. Click **"Deploy Now"**.

---

## ⚙️ Step 3: Add Environment Variables in Railway

Go to your Railway project **Dashboard -> Service Settings -> Variables** and add:

| Variable | Recommended Production Value | Notes |
| :--- | :--- | :--- |
| `APP_ENV` | `production` | Enables production JSON logging |
| `LOG_LEVEL` | `INFO` | Standard structured logging |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/commerce.db` | Or Railway PostgreSQL URL |
| `QDRANT_COLLECTION` | `transact_products` | Collection name |
| `RAZORPAY_KEY_ID` | `rzp_test_...` | Your Razorpay API Key ID |
| `RAZORPAY_KEY_SECRET` | `...` | Your Razorpay Secret Key |
| `RAZORPAY_WEBHOOK_SECRET` | `MySecret12345` | Same secret used in Razorpay Webhook |
| `QDRANT_URL` | `https://xxx.qdrant.tech:6333` | Optional Qdrant Cloud URL |
| `QDRANT_API_KEY` | `...` | Optional Qdrant Cloud API Key |
| `LANGSMITH_API_KEY` | `lsv2_pt_...` | Optional LangSmith API Key |

---

## 🌐 Step 4: Generate Public Domain

1. In Railway, click **Settings -> Networking -> Generate Domain**.
2. You will get a live URL, e.g.: `https://transact-ai-production.up.railway.app`
3. Test your live health endpoint:
   ```bash
   curl https://transact-ai-production.up.railway.app/health
   ```
4. Access interactive Swagger API Docs:
   `https://transact-ai-production.up.railway.app/docs`

---

## 💳 Step 5: Connect Razorpay Webhook

1. Go to [Razorpay Dashboard](https://dashboard.razorpay.com) -> **Settings** -> **Webhooks** -> **Add New Webhook**.
2. **Webhook URL**:
   `https://<YOUR-RAILWAY-DOMAIN>/api/v1/payments/webhook`
3. **Secret**: Enter the exact same secret set in `RAZORPAY_WEBHOOK_SECRET`.
4. **Active Events**:
   - `payment.captured`
   - `order.paid`
   - `payment.failed`
5. Click **Create Webhook**!

🎉 Your Transact AI autonomous commerce engine is now 100% live in production!
