"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import Script from "next/script";
import {
  Layers,
  Zap,
  ShieldCheck,
  CreditCard,
  Cpu,
  Copy,
  CheckCircle2,
  ExternalLink,
  ChevronRight,
  ArrowLeft,
  Filter,
  Maximize2,
  Code2,
  Eye,
  Terminal,
  Activity,
  GitBranch,
  Database,
  Store,
  Compass,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";

interface BlueprintItem {
  id: string;
  number: string;
  category: "gateway" | "latency" | "guardrails" | "settlement";
  categoryLabel: string;
  title: string;
  purpose: string;
  mermaidCode: string;
  metrics: { label: string; value: string; color?: string }[];
  invariants: string[];
}

const BLUEPRINTS: BlueprintItem[] = [
  {
    id: "universal-gateway",
    number: "01",
    category: "gateway",
    categoryLabel: "Multi-Host Ingestion",
    title: "Universal Autonomous Commerce Gateway Architecture",
    purpose:
      "Connects frontier conversational AI models (Claude, ChatGPT, Gemini) to real-world local merchants and quick-commerce providers without exposing raw databases or proprietary APIs. External tool calls are strictly normalized into a canonical schema.",
    metrics: [
      { label: "Supported Hosts", value: "Claude, ChatGPT, Gemini" },
      { label: "Protocol", value: "MCP & OpenAPI" },
      { label: "Execution Model", value: "Zero Direct DB Exposure" },
    ],
    invariants: [
      "No frontier AI host communicates directly with PostgreSQL or Payment Gateways.",
      "All multi-provider listings are transformed into canonical ProductSchema instances.",
      "Deterministically verified inventory prevents model hallucinations from reaching checkout.",
    ],
    mermaidCode: `graph TB
    subgraph Hosts["1. Multi-Host AI Ingestion Layer"]
        C1["Claude (Model Context Protocol - stdio / HTTP)"]
        C2["ChatGPT (OpenAPI Actions / Custom GPT)"]
        C3["Google Gemini (Function Calling / Tools)"]
    end

    subgraph Gateway["2. TransactAI Deterministic Gateway Core"]
        MCP["MCP Protocol Router & JSON-RPC Gateway"]
        INTENT["Structured Intent Parser (BuyerIntentSchema)"]
        DISC["FastEmbed Semantic Vector Search (<85ms)"]
        GATE["Atomic Pre-Flight Gatekeeper & Policy Engine"]
        GRAPH["LangGraph Commerce State Machine"]
    end

    subgraph Adapters["3. Canonical Provider Adapters"]
        LA["LocalMerchantAdapter (PostgreSQL + Pincode Radius)"]
        BA["BlinkitAdapter (Dark Store 10-min Delivery)"]
        ZA["ZeptoAdapter (Instant Grocery Quick-Commerce)"]
        SA["SwiggyAdapter (Food & Grocery Marketplace)"]
    end

    subgraph Storage["4. Financial & Storage Settlement Layer"]
        DB[("PostgreSQL on Railway<br/>(Merchants, Orders, Payments, Audit)")]
        VEC[("Qdrant Cloud Vector DB<br/>(384d BGE Embeddings)")]
        RZP["Razorpay Hosted Checkout & Webhooks (HMAC-SHA256)"]
    end

    Hosts --> MCP
    MCP --> INTENT
    INTENT --> DISC
    DISC --> GATE
    GATE --> GRAPH
    GRAPH --> LA & BA & ZA & SA
    LA & BA & ZA & SA --> DB & VEC
    GRAPH --> RZP`,
  },
  {
    id: "vector-discovery",
    number: "02",
    category: "latency",
    categoryLabel: "Sub-85ms Engine",
    title: "<85ms Hybrid Semantic Vector Discovery Pipeline",
    purpose:
      "Compound agent latency destroys UX in multi-turn shopping. By combining local in-memory FastEmbed inference (bge-small-en-v1.5) with parallel Qdrant Cloud HNSW searches and strict payload pruning, TransactAI achieves a 78.05 ms production trace.",
    metrics: [
      { label: "P95 Discovery Latency", value: "11.23 - 36.86 ms", color: "text-emerald-400" },
      { label: "Embedding Latency", value: "~14 ms (FastEmbed)" },
      { label: "Payload Reduction", value: "1.15 MB ➔ 20 KB (98.2%)" },
    ],
    invariants: [
      "In-memory FastEmbed eliminates cold remote network API calls for embedding generation.",
      "Parallel fan-out across vector semantic search and relational catalog filters.",
      "Payload trimming caps candidate lists to Top 5 items, preventing state serialization bloat.",
    ],
    mermaidCode: `graph LR
    subgraph Input["1. Buyer Prompt"]
        P["User Natural Language Prompt:<br/>'1kg Rasgulla under ₹500 in 110001'"]
    end

    subgraph Embed["2. Local FastEmbed Engine"]
        FE["FastEmbed (bge-small-en-v1.5)<br/>384-dim dense vector<br/>⏱️ ~14ms (In-Memory, 0ms Network)"]
    end

    subgraph Search["3. Parallel Fan-Out Discovery"]
        QD[("Qdrant Cloud Cluster<br/>HNSW Cosine Vector Index<br/>⏱️ ~35ms")]
        PG[("PostgreSQL Railway<br/>Pincode & Merchant Filter<br/>⏱️ ~18ms")]
    end

    subgraph Optimization["4. Payload Optimization"]
        TRIM["Candidate Payload Trimmer<br/>Capped to Top 5 items<br/>1.15 MB ➔ 20 KB payload"]
    end

    subgraph Output["5. LangSmith Verified Trace"]
        OUT["Validated Candidates<br/>⚡ Total Latency: ~78.05 ms (< 85 ms Target)"]
    end

    P --> FE
    FE --> QD & PG
    QD & PG --> TRIM
    TRIM --> OUT`,
  },
  {
    id: "atomic-gatekeeper",
    number: "03",
    category: "guardrails",
    categoryLabel: "Deterministic Guardrails",
    title: "Atomic Pre-Flight Gatekeeper & Spending Policy Engine",
    purpose:
      "Never permit an LLM to initiate payment on unverified inventory or exceed buyer-defined financial caps. The Pre-Flight Gatekeeper combines authoritative database truth checks with mathematical spending limit verification as an atomic operation.",
    metrics: [
      { label: "Verification Speed", value: "< 12 ms" },
      { label: "Budget Precision", value: "Exact Subunit (Paise)" },
      { label: "Policy Enforcement", value: "100% Deterministic" },
    ],
    invariants: [
      "Zero orders proceed to payment creation without passing both Truth & Policy checks.",
      "Financial calculations strictly evaluate integer paise (no floating-point rounding errors).",
      "Violations immediately emit structured audit logs and trigger the Recovery Engine.",
    ],
    mermaidCode: `graph TD
    PROPOSAL["Agent Proposed Product Candidate"] --> GATE["Atomic Gatekeeper Service (app/services/gatekeeper_service.py)"]

    subgraph Verification["Step 1: Authoritative Truth Verification"]
        GATE --> V1["Live DB Price Check (Paise precision)"]
        GATE --> V2["Inventory Stock Check (Qty >= Requested)"]
        GATE --> V3["Freshness Tier Verification (Real-time vs Cached)"]
        GATE --> V4["Fulfillment SLA Validation (Prep time + Delivery)"]
    end

    subgraph Policy["Step 2: Deterministic Spending Limits"]
        GATE --> P1{"Per-Transaction Limit<br/>Amount <= Max Per Tx?"}
        GATE --> P2{"Daily Spending Budget<br/>Spent Today + Amount <= Daily Limit?"}
        GATE --> P3{"Category Whitelist<br/>Category in Allowed Categories?"}
    end

    V1 & V2 & V3 & V4 --> EVAL{"Both Checks Pass?"}
    P1 & P2 & P3 --> EVAL

    EVAL -->|"YES"| ALLOW["✅ Decision: ALLOW<br/>Emit PREFLIGHT_PASSED Audit<br/>Proceed to Human Confirmation"]
    EVAL -->|"NO"| BLOCK["🚫 Decision: BLOCK<br/>Emit POLICY_VIOLATED Audit<br/>Trigger Recovery Engine"]`,
  },
  {
    id: "two-stage-ranking",
    number: "04",
    category: "latency",
    categoryLabel: "Algorithmic Fairness",
    title: "Two-Stage Multi-Criteria Ranking Pipeline",
    purpose:
      "Guarantees absolute commercial neutrality. Hard constraints (budget cap, delivery radius, out of stock) immediately disqualify items regardless of provider popularity. Surviving candidates are ranked using an objective multi-factor formula.",
    metrics: [
      { label: "Ranking Strategy", value: "Two-Stage Pipeline" },
      { label: "Commercial Bias", value: "0% Algorithmic Neutrality" },
      { label: "Factors Evaluated", value: "Budget, SLA, Cosine, Freshness" },
    ],
    invariants: [
      "Hard constraint disqualification precedes all scoring — invalid products are never ranked.",
      "Scoring weights prioritize consumer value: 35% Budget Savings, 30% Delivery Speed, 20% Relevance, 15% Freshness.",
      "Results across local stores and quick-commerce dark stores are evaluated on an identical mathematical scale.",
    ],
    mermaidCode: `graph TD
    ALL["Raw Candidate Pool (Sharma Sweets, Blinkit, Zepto, Swiggy)"] --> STAGE1{"Stage 1: Hard Constraint Filter"}

    STAGE1 -->|"Price > Budget"| DROP1["❌ Excluded (Exceeds Budget)"]
    STAGE1 -->|"Pincode Out of Radius"| DROP2["❌ Excluded (Cannot Deliver)"]
    STAGE1 -->|"Stock = 0"| DROP3["❌ Excluded (Out of Stock)"]

    STAGE1 -->|"Passes All Hard Constraints"| STAGE2["Stage 2: Multi-Factor Weighted Scoring"]

    subgraph Scoring["Deterministic Formula"]
        STAGE2 --> S1["Budget Fit Score (0.35) — Maximum savings"]
        STAGE2 --> S2["Fulfillment Speed (0.30) — Fastest delivery/prep"]
        STAGE2 --> S3["Semantic Match (0.20) — Vector cosine distance"]
        STAGE2 --> S4["Data Freshness (0.15) — Verified live tier"]
    end

    S1 & S2 & S3 & S4 --> RANK["🏆 Ranked Candidates (1st, 2nd, 3rd) Presented to User"]`,
  },
  {
    id: "langgraph-state",
    number: "05",
    category: "guardrails",
    categoryLabel: "Agent State Machine",
    title: "Autonomous Commerce State Graph (LangGraph Execution)",
    purpose:
      "Models the complete transaction as a deterministic, typed state graph with state rollback, conditional branch routing, and a mandatory Human-in-the-Loop (HITL) confirmation node before financial link generation.",
    metrics: [
      { label: "Graph Engine", value: "LangGraph Core" },
      { label: "Total Loop Latency", value: "70.06 ms (End-to-End)" },
      { label: "Safety Gate", value: "HITL User Phone & Summary Confirmation" },
    ],
    invariants: [
      "Every step updates a strictly typed AgentCommerceState schema.",
      "Failure at discovery or gatekeeper automatically routes to the constraint recovery node.",
      "Payment nodes cannot execute without human confirmation in state history.",
    ],
    mermaidCode: `graph TD
    START(["User Prompt"]) --> N1["1. parse_intent_node<br/>Extract item, budget, pincode"]
    N1 --> N2["2. multi_provider_discovery_node<br/>Qdrant + DB multi-search"]
    
    N2 --> C1{"Candidates Found?"}
    C1 -->|"No"| N_REC["recovery_recommender_node<br/>Relax constraints across 4 dimensions"]
    C1 -->|"Yes"| N3["3. gatekeeper_verification_node<br/>Live verification & policy checks"]

    N3 --> C2{"Gatekeeper Result"}
    C2 -->|"BLOCK"| N_REC
    C2 -->|"ALLOW"| N4["4. order_proposal_node<br/>Format quote, SLA & savings"]

    N4 --> HITL{{"⏸️ Human-in-the-Loop Gate<br/>User reviews & confirms with Phone"}}
    HITL -->|"Confirmed"| N5["5. razorpay_order_node<br/>Generate secure checkout link"]
    HITL -->|"Rejected / Cancelled"| END(["End Session / Cancelled"])
    N5 --> END
    N_REC --> END`,
  },
  {
    id: "razorpay-settlement",
    number: "06",
    category: "settlement",
    categoryLabel: "Cryptographic Settlement",
    title: "Razorpay Cryptographic Payment & Webhook Settlement Lifecycle",
    purpose:
      "All financial values strictly use currency subunits (paise integers) to avoid floating-point drift. Double verification via client HMAC-SHA256 signature checking and asynchronous server webhooks ensures 100% settlement accuracy with idempotency keys.",
    metrics: [
      { label: "Gateway", value: "Razorpay Hosted Checkout" },
      { label: "Security", value: "HMAC-SHA256 Cryptographic Digest" },
      { label: "Precision", value: "Paise Integers (₹1.00 = 100 paise)" },
    ],
    invariants: [
      "Order creation, signature verification, and webhook handling enforce idempotency keys.",
      "Database records pay_... transaction ID across both orders and payments tables upon verification.",
      "Amounts are calculated in paise integers to eliminate floating point rounding discrepancies.",
    ],
    mermaidCode: `sequenceDiagram
    autonumber
    actor Buyer as 🛒 Buyer
    participant Frontend as 🖥️ Hosted Checkout (/pay/{order_id})
    participant Core as ⚙️ TransactAI Server
    participant DB as 🗄️ PostgreSQL (Railway)
    participant RZP as 💳 Razorpay Gateway

    Buyer->>Frontend: Opens hosted payment page
    Frontend->>Core: GET /api/v1/payments/orders/{id}
    Core->>DB: Fetch order (amount: 4000 paise = ₹40.00)
    Core-->>Frontend: Render order summary & Razorpay options

    alt Razorpay Live Checkout
        Buyer->>Frontend: Pays via UPI / Card
        Frontend->>RZP: Process payment
        RZP-->>Frontend: Return razorpay_payment_id & signature
        Frontend->>Core: POST /api/v1/payments/verify-signature
        Note over Core: HMAC-SHA256 Cryptographic Check
        Core->>DB: UPDATE payments SET status='success', transaction_id='pay_...'
        Core->>DB: UPDATE orders SET status='order_created', transaction_id='pay_...'
    else Asynchronous Webhook Settlement
        RZP->>Core: POST /api/v1/payments/webhook (payment.captured)
        Note over Core: Webhook Signature & Idempotency Check
        Core->>DB: Settle payment & order if not already settled
    end

    Core-->>Frontend: Payment Verified ✅
    Frontend-->>Buyer: Show Success + "Track Order in Buyer Console"`,
  },
  {
    id: "audit-trail",
    number: "07",
    category: "settlement",
    categoryLabel: "Observability & Compliance",
    title: "3-Layer Audit Trail & Order Lifecycle Architecture",
    purpose:
      "Provides complete regulatory compliance, fraud prevention, and operational debugging by writing every agent action across three distinct observability tiers while transitioning orders through an explicit finite state machine.",
    metrics: [
      { label: "Audit Tiers", value: "3 (DB Ledger, JSON Logs, LangSmith)" },
      { label: "Compliance", value: "Tamper-Evident Event Append" },
      { label: "Tracing", value: "Distributed Span Context" },
    ],
    invariants: [
      "Layer 1: Immutable audit_events table stores user_id, order_id, amount, and reasons.",
      "Layer 2: Structlog JSON logger outputs machine-readable logs for SIEM & ELK stacks.",
      "Layer 3: Distributed LangSmith tracing records latency, tokens, and span metadata.",
    ],
    mermaidCode: `graph TD
    ACTION["Agent Commerce Action (Intent / Gatekeeper / Payment / Fulfillment)"] --> ENGINE["3-Layer Production Audit Engine (app/services/audit_service.py)"]

    subgraph Layer1["Layer 1: Immutable DB Ledger"]
        ENGINE --> L1["audit_events Table<br/>(event_type, timestamp, user_id, order_id, amount, reason, metadata)"]
    end

    subgraph Layer2["Layer 2: Structured JSON Logs"]
        ENGINE --> L2["Structlog JSON Logger<br/>(Machine-readable stdout/file for ELK/Datadog)"]
    end

    subgraph Layer3["Layer 3: Distributed Observability"]
        ENGINE --> L3["LangSmith Traces & Run Tags<br/>(Latency profiling, token tracking, eval)"]
    end

    subgraph StateMachine["Complete Order State Machine"]
        S1["discovered"] --> S2["verified"]
        S2 --> S3["user_confirmed"]
        S3 --> S4["payment_pending"]
        S4 --> S5A["payment_success"]
        S4 -.-> S5B["payment_failed"]
        S5A --> S6["order_created"]
        S6 --> S7A["ready_for_pickup / out_for_delivery"]
        S6 -.-> S7B["cancelled"]
        S7A --> S8["completed"]
    end

    ENGINE --> StateMachine`,
  },
  {
    id: "constraint-relaxation",
    number: "08",
    category: "guardrails",
    categoryLabel: "Autonomous Recovery",
    title: "Multi-Dimensional Constraint Relaxation & Autonomous Recovery",
    purpose:
      "When an exact query yields zero matches (e.g. ₹300 budget in 15 mins), the agent never dead-ends. It automatically explores four orthogonal relaxation dimensions to propose relevant, actionable alternatives to the user.",
    metrics: [
      { label: "Relaxation Dimensions", value: "Price, SLA, Provider, Category" },
      { label: "Dead-End Rate", value: "0% Agent Abandonment" },
      { label: "Response", value: "Actionable Alternative Quotes" },
    ],
    invariants: [
      "Price headroom explores +10% to +25% above budget if higher quality options exist.",
      "Timeline extension switches from quick-commerce 15m to standard 30m delivery.",
      "Cross-platform switching queries alternate partner inventories when local stock is exhausted.",
    ],
    mermaidCode: `graph TD
    FAIL["Exact Criteria Yields 0 Matches<br/>(e.g. 'Rasgulla under ₹300 in 15 mins')"] --> ENG["Autonomous Recovery Engine (app/services/recovery_service.py)"]

    subgraph Four_Dimensions["4-Way Autonomous Constraint Relaxation"]
        ENG --> D1["1. Price Headroom (+10-25%)<br/>'₹300 mein nahi hai, par ₹350 mein Zepto par available hai'"]
        ENG --> D2["2. Timeline / SLA Extension<br/>'15 min mein nahi hai, par 30 min standard delivery mein available hai'"]
        ENG --> D3["3. Cross-Platform Switching<br/>'Sharma Sweets out of stock hai, par Blinkit par in stock hai'"]
        ENG --> D4["4. Category Substitution<br/>'Rasgulla nahi mila, par Gulab Jamun ₹280 mein available hai'"]
    end

    D1 & D2 & D3 & D4 --> RANK["Rank & Tag Alternatives Clearly"]
    RANK --> AGENT["Agent Message to User with Actionable Alternatives"]`,
  },
  {
    id: "dual-mode-bridge",
    number: "09",
    category: "gateway",
    categoryLabel: "Protocol Bridge",
    title: "Dual-Mode Protocol Bridge: Local STDIO vs Remote Streamable HTTP",
    purpose:
      "Bridges the architectural gap between local desktop agent processes (Claude Desktop via stdio pipes) and remote cloud-native assistants (ChatGPT Actions and Claude.ai Web via HTTPS JSON-RPC 2.0).",
    metrics: [
      { label: "Local Transport", value: "Standard Input / Output Pipes" },
      { label: "Remote Transport", value: "Streamable HTTP & SSE" },
      { label: "Tool Schema", value: "100% Cross-Compatible" },
    ],
    invariants: [
      "Identical tools.py registry powers both local stdio execution and remote webhooks.",
      "Zero re-engineering required when migrating from Claude Desktop to cloud enterprise agents.",
      "Stateless JSON-RPC request-response cycles with cryptographic session validation.",
    ],
    mermaidCode: `graph TB
    subgraph Clients["Heterogeneous AI Clients"]
        LOCAL["Claude Desktop App (Local Laptop)"]
        REMOTE["ChatGPT Custom GPT / Claude.ai Web (Cloud Servers)"]
    end

    subgraph Dual_Mode["Dual-Mode Transport Bridge"]
        STDIO["STDIO Transport Handler<br/>(Reads stdin, writes stdout)"]
        HTTP["Streamable HTTP / JSON-RPC Handler<br/>(POST /mcp & /execute-tool)"]
    end

    subgraph Registry["Unified MCP Commerce Tools Registry"]
        REG["tools.py Registry<br/>• transact_search_catalog<br/>• transact_verify_order_preflight<br/>• transact_create_order_payment<br/>• transact_register_merchant"]
    end

    subgraph Core["Execution Core"]
        SERVICES["PostgreSQL + Qdrant + Razorpay"]
    end

    LOCAL -->|"Process Pipes (stdin/stdout)"| STDIO
    REMOTE -->|"HTTPS JSON-RPC 2.0 / OpenAPI"| HTTP
    STDIO & HTTP --> REG
    REG --> SERVICES`,
  },
  {
    id: "merchant-onboarding",
    number: "10",
    category: "settlement",
    categoryLabel: "Merchant Pipeline",
    title: "Merchant Onboarding, FastEmbed Vectorization & Payout Pipeline",
    purpose:
      "Enables local physical merchants to register their store and catalog in under 3 minutes. The pipeline automatically persists store coordinates, fulfillment settings, and bank settlement details into PostgreSQL while vectorizing products into Qdrant Cloud.",
    metrics: [
      { label: "Onboarding Time", value: "< 3 Minutes (6 Steps)" },
      { label: "Vector Processing", value: "Instant FastEmbed BAAI/bge" },
      { label: "Settlement Ready", value: "UPI & Bank IFSC Verification" },
    ],
    invariants: [
      "Auto-generates sk_live_... merchant API keys for POS and catalog management.",
      "Catalog items are vectorized asynchronously and immediately searchable by AI agents in <85ms.",
      "Stores can configure Doorstep Delivery, Store Pickup, or Both within their delivery radius.",
    ],
    mermaidCode: `graph LR
    subgraph Wizard["6-Step Merchant Wizard (/merchant/register)"]
        W1["1. Identity & Name"] --> W2["2. Location & Radius"]
        W2 --> W3["3. Owner Contacts"]
        W3 --> W4["4. Catalog & Pricing"]
        W4 --> W5["5. UPI & Bank Details"]
        W5 --> W6["6. Launch Celebration"]
    end

    subgraph Ingestion["Backend Ingestion Pipeline"]
        POST["POST /api/v1/merchants"]
        FE["FastEmbed Engine<br/>Vectorize Product Description"]
    end

    subgraph Storage["Dual-Database Persistence"]
        PG[("PostgreSQL (Railway)<br/>• merchants (Store info + Bank Payouts)<br/>• products (Price, Units, Stock)<br/>• sk_live_... API Keys")]
        QD[("Qdrant Cloud<br/>• 384d Dense Vector Index<br/>• Ready for AI Search in <85ms")]
    end

    W6 --> POST
    POST --> PG
    POST --> FE --> QD`,
  },
];

function DiagramCard({
  item,
  isMermaidReady,
}: {
  item: BlueprintItem;
  isMermaidReady: boolean;
}) {
  const [activeTab, setActiveTab] = useState<"visual" | "code">("visual");
  const [copied, setCopied] = useState(false);
  const [svgContent, setSvgContent] = useState<string>("");
  const [renderError, setRenderError] = useState<string | null>(null);
  const [isRendering, setIsRendering] = useState<boolean>(true);
  const { showToast } = useToast();

  useEffect(() => {
    let isMounted = true;

    if (!isMermaidReady || typeof window === "undefined" || !(window as any).mermaid) {
      return;
    }

    const renderDiagram = async () => {
      try {
        setIsRendering(true);
        setRenderError(null);
        const uniqueId = `mermaid-${item.id}-${Math.random().toString(36).substring(2, 9)}`;
        const { svg } = await (window as any).mermaid.render(uniqueId, item.mermaidCode);
        if (isMounted) {
          setSvgContent(svg);
          setIsRendering(false);
        }
      } catch (err: any) {
        console.error("Mermaid render error for:", item.id, err);
        if (isMounted) {
          setRenderError(err?.message || "Failed to render diagram");
          setIsRendering(false);
        }
      }
    };

    renderDiagram();

    return () => {
      isMounted = false;
    };
  }, [item.mermaidCode, item.id, isMermaidReady]);

  const handleCopyCode = async () => {
    try {
      await navigator.clipboard.writeText(item.mermaidCode);
      setCopied(true);
      showToast(`Mermaid source for Blueprint #${item.number} copied to clipboard.`, "success");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      showToast("Could not copy to clipboard. Please copy manually from the code view.", "error");
    }
  };

  const openInMermaidLive = () => {
    const encoded = encodeURIComponent(item.mermaidCode);
    window.open(`https://mermaid.live/edit#code=${encoded}`, "_blank");
  };

  return (
    <article
      id={item.id}
      className="scroll-mt-28 bg-[#18181B] border border-[#27272A] rounded-3xl overflow-hidden shadow-2xl transition-all duration-300 hover:border-[#3F3F46]"
    >
      {/* Card Header Lockup */}
      <div className="p-6 sm:p-8 border-b border-[#27272A] bg-gradient-to-r from-[#18181B] via-[#202024] to-[#18181B]">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="px-3 py-1 rounded-full text-xs font-mono font-black bg-[#FF203D]/10 border border-[#FF203D]/30 text-[#FF203D]">
                Blueprint #{item.number}
              </span>
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-white/5 border border-white/10 text-neutral-300">
                {item.categoryLabel}
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
              {item.title}
            </h2>
            <p className="text-xs sm:text-sm text-neutral-400 max-w-3xl leading-relaxed">
              {item.purpose}
            </p>
          </div>

          {/* Action Tabs & Controls */}
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <div className="inline-flex p-1 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-bold">
              <button
                type="button"
                onClick={() => setActiveTab("visual")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                  activeTab === "visual"
                    ? "bg-[#FF203D] text-white shadow-sm"
                    : "text-neutral-400 hover:text-white"
                }`}
              >
                <Eye className="w-3.5 h-3.5" />
                <span>Visual Flow</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("code")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                  activeTab === "code"
                    ? "bg-[#FF203D] text-white shadow-sm"
                    : "text-neutral-400 hover:text-white"
                }`}
              >
                <Code2 className="w-3.5 h-3.5" />
                <span>Mermaid Code</span>
              </button>
            </div>

            <button
              type="button"
              onClick={handleCopyCode}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-extrabold text-neutral-200 transition-all cursor-pointer shadow-xs"
              title="Copy Mermaid source code"
            >
              {copied ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-[#FF7A18]" />
                  <span>Copy</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={openInMermaidLive}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-bold text-neutral-300 transition-all cursor-pointer"
              title="Open diagram in Mermaid Live Editor"
            >
              <ExternalLink className="w-3.5 h-3.5 text-neutral-400" />
              <span>Live Editor</span>
            </button>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-6 mt-6 border-t border-[#27272A]/80">
          {item.metrics.map((m, idx) => (
            <div
              key={idx}
              className="p-3 rounded-2xl bg-neutral-900/60 border border-neutral-800/80 space-y-0.5"
            >
              <span className="text-[10px] font-mono uppercase tracking-wider text-neutral-400">
                {m.label}
              </span>
              <div className={`text-xs font-black font-mono ${m.color || "text-neutral-200"}`}>
                {m.value}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="p-6 sm:p-8 space-y-6">
        {activeTab === "visual" ? (
          <div className="relative rounded-2xl bg-[#0D0D0E] border border-neutral-800/90 p-4 sm:p-8 min-h-[300px] flex items-center justify-center overflow-x-auto">
            {isRendering ? (
              <div className="flex flex-col items-center gap-3 py-16 text-neutral-400">
                <div className="w-8 h-8 rounded-full border-2 border-[#FF203D] border-t-transparent animate-spin" />
                <span className="text-xs font-mono">Rendering vector architecture diagram...</span>
              </div>
            ) : renderError ? (
              <div className="p-6 rounded-xl bg-red-950/40 border border-red-800/50 text-center space-y-3 max-w-md">
                <div className="text-xs font-bold text-red-400">Diagram rendering fallback</div>
                <p className="text-xs text-neutral-400">
                  Interactive SVG rendering encountered an issue. You can inspect the Mermaid syntax
                  directly or open it in Mermaid Live.
                </p>
                <div className="flex justify-center gap-3">
                  <button
                    type="button"
                    onClick={() => setActiveTab("code")}
                    className="px-3 py-1.5 rounded-lg bg-neutral-800 text-xs text-white"
                  >
                    View Source Code
                  </button>
                  <button
                    type="button"
                    onClick={openInMermaidLive}
                    className="px-3 py-1.5 rounded-lg bg-[#FF203D] text-xs text-white"
                  >
                    Open in Live Editor
                  </button>
                </div>
              </div>
            ) : (
              <div
                className="w-full flex justify-center items-center mermaid-svg-wrapper [&>svg]:max-w-full [&>svg]:h-auto [&>svg]:drop-shadow-md"
                dangerouslySetInnerHTML={{ __html: svgContent }}
              />
            )}
          </div>
        ) : (
          <div className="rounded-2xl bg-[#0D0D0E] border border-neutral-800 p-4 sm:p-6 overflow-x-auto shadow-inner">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-neutral-800/80 text-[11px] font-mono text-neutral-400">
              <span>Mermaid v10 Flowchart Definition</span>
              <button
                type="button"
                onClick={handleCopyCode}
                className="text-[#FF7A18] hover:text-[#FF203D] transition-colors cursor-pointer"
              >
                {copied ? "Copied!" : "Click to Copy"}
              </button>
            </div>
            <pre className="font-mono text-xs text-neutral-200 leading-relaxed overflow-x-auto">
              <code>{item.mermaidCode}</code>
            </pre>
          </div>
        )}

        {/* Technical Invariants Breakdown */}
        <div className="p-5 rounded-2xl bg-[#202024]/70 border border-[#27272A] space-y-3">
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-neutral-300">
            <ShieldCheck className="w-4 h-4 text-[#FF7A18]" />
            <span>Core Architectural Invariants & Guarantees</span>
          </div>
          <ul className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {item.invariants.map((inv, idx) => (
              <li
                key={idx}
                className="p-3 rounded-xl bg-neutral-950/40 border border-neutral-800/60 text-xs text-neutral-300 flex items-start gap-2.5 leading-relaxed"
              >
                <div className="w-1.5 h-1.5 rounded-full bg-[#FF203D] shrink-0 mt-1.5" />
                <span>{inv}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </article>
  );
}

export default function ArchitectureDevDocsPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [isMermaidReady, setIsMermaidReady] = useState<boolean>(false);
  const { showToast } = useToast();

  const handleMermaidReady = () => {
    if (typeof window !== "undefined" && (window as any).mermaid) {
      try {
        (window as any).mermaid.initialize({
          startOnLoad: false,
          theme: "dark",
          darkMode: true,
          themeVariables: {
            darkMode: true,
            background: "#0D0D0E",
            primaryColor: "#FF203D",
            primaryTextColor: "#F4F4F5",
            primaryBorderColor: "#FF7A18",
            lineColor: "#A1A1AA",
            secondaryColor: "#1E1E1E",
            tertiaryColor: "#27272A",
            mainBkg: "#18181B",
            nodeBorder: "#FF7A18",
            clusterBkg: "#111114",
            clusterBorder: "#3F3F46",
            titleColor: "#FFFFFF",
            edgeLabelBackground: "#27272A",
            actorBkg: "#1F2937",
            actorBorder: "#3B82F6",
            actorTextColor: "#FFFFFF",
            actorLineColor: "#6B7280",
            signalColor: "#E5E7EB",
            signalTextColor: "#FFFFFF",
          },
          securityLevel: "loose",
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        });
        setIsMermaidReady(true);
      } catch (e) {
        console.error("Failed to initialize Mermaid:", e);
      }
    }
  };

  const filteredBlueprints = BLUEPRINTS.filter((b) => {
    if (selectedCategory === "all") return true;
    return b.category === selectedCategory;
  });

  const categories = [
    { id: "all", label: "All Blueprints", count: BLUEPRINTS.length },
    {
      id: "gateway",
      label: "Ingestion & Gateways",
      count: BLUEPRINTS.filter((b) => b.category === "gateway").length,
    },
    {
      id: "latency",
      label: "Sub-85ms & Ranking",
      count: BLUEPRINTS.filter((b) => b.category === "latency").length,
    },
    {
      id: "guardrails",
      label: "Guardrails & State Machine",
      count: BLUEPRINTS.filter((b) => b.category === "guardrails").length,
    },
    {
      id: "settlement",
      label: "Settlement & Audit Ledger",
      count: BLUEPRINTS.filter((b) => b.category === "settlement").length,
    },
  ];

  const handleCopyAll = async () => {
    const allMarkdown = BLUEPRINTS.map(
      (b) => `## ${b.number}. ${b.title}\n\n${b.purpose}\n\n\`\`\`mermaid\n${b.mermaidCode}\n\`\`\`\n`
    ).join("\n---\n\n");

    try {
      await navigator.clipboard.writeText(allMarkdown);
      showToast("All 10 Blueprints copied to clipboard with full Mermaid code!", "success");
    } catch {
      showToast("Could not copy to clipboard.", "error");
    }
  };

  return (
    <div className="min-h-screen bg-[#0D0D0E] text-neutral-100 selection:bg-[#FF203D] selection:text-white">
      {/* Load Mermaid.js from CDN */}
      <Script
        src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"
        strategy="afterInteractive"
        onReady={handleMermaidReady}
      />

      {/* Top Breadcrumb Header */}
      <div className="border-b border-neutral-800 bg-[#121214]/90 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs font-mono">
            <Link
              href="/developer"
              className="text-neutral-400 hover:text-white transition-colors flex items-center gap-1.5"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>DevDocs</span>
            </Link>
            <ChevronRight className="w-3 h-3 text-neutral-600" />
            <span className="text-[#FF203D] font-bold">System Architecture Blueprints</span>
          </div>

          <div className="flex items-center gap-3">
            <a
              href="https://github.com/Sahil9205/Transact-Ai/blob/main/docs/architecture_flowcharts.md"
              target="_blank"
              rel="noreferrer"
              className="hidden sm:inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-bold text-neutral-200 transition-all cursor-pointer"
            >
              <GitBranch className="w-3.5 h-3.5 text-[#FF7A18]" />
              <span>View docs/architecture_flowcharts.md</span>
              <ExternalLink className="w-3 h-3 text-neutral-400" />
            </a>

            <button
              type="button"
              onClick={handleCopyAll}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-[#FF203D] hover:bg-[#E01B34] text-xs font-black text-white transition-all cursor-pointer shadow-md"
            >
              <Copy className="w-3.5 h-3.5" />
              <span>Copy All (10)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Hero Header Section */}
      <header className="relative pt-16 pb-12 border-b border-neutral-800 bg-gradient-to-b from-[#18181B] via-[#121214] to-[#0D0D0E] overflow-hidden">
        {/* Glow ambient background circles */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-[#FF203D]/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-10 right-1/4 w-96 h-96 bg-[#FF7A18]/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#FF203D]/10 border border-[#FF203D]/30 text-xs font-mono font-black text-[#FF203D]">
            <Layers className="w-3.5 h-3.5" />
            <span>10 Production Architecture Flowcharts & System Blueprints</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-white max-w-4xl leading-tight">
            Transact<span className="text-[#FF203D]">AI</span> System Design &amp; Architectural Specifications
          </h1>

          <p className="text-sm sm:text-base text-neutral-400 max-w-3xl leading-relaxed">
            Every transaction executed by TransactAI is governed by deterministic, verifiable code.
            Explore interactive visual representations of our multi-host protocol ingestion, sub-85ms
            FastEmbed vector discovery, atomic pre-flight gatekeeping, LangGraph state graph, and
            Razorpay HMAC-SHA256 settlement lifecycles.
          </p>

          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4">
            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-1">
              <span className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider">
                Discovery Latency
              </span>
              <div className="text-xl font-black font-mono text-emerald-400">78.05 ms</div>
              <p className="text-[11px] text-neutral-400">Verified via LangSmith traces</p>
            </div>

            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-1">
              <span className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider">
                Gatekeeper Checks
              </span>
              <div className="text-xl font-black font-mono text-amber-400">100% Deterministic</div>
              <p className="text-[11px] text-neutral-400">Zero unverified AI debits</p>
            </div>

            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-1">
              <span className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider">
                Audit Observability
              </span>
              <div className="text-xl font-black font-mono text-sky-400">3 Distinct Layers</div>
              <p className="text-[11px] text-neutral-400">DB + Structlog + LangSmith</p>
            </div>

            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-1">
              <span className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider">
                Financial Currency
              </span>
              <div className="text-xl font-black font-mono text-[#FF7A18]">Paise Integers</div>
              <p className="text-[11px] text-neutral-400">Zero float rounding drift</p>
            </div>
          </div>
        </div>
      </header>

      {/* Category Filter Navigation Bar */}
      <section className="sticky top-16 z-20 bg-[#0D0D0E]/95 backdrop-blur-md border-b border-neutral-800 py-3.5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0 scrollbar-none">
            {categories.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => setSelectedCategory(c.id)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
                  selectedCategory === c.id
                    ? "bg-[#FF203D] text-white shadow-sm"
                    : "bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-white hover:bg-neutral-800"
                }`}
              >
                <span>{c.label}</span>
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-md font-mono ${
                    selectedCategory === c.id
                      ? "bg-black/20 text-white"
                      : "bg-neutral-800 text-neutral-400"
                  }`}
                >
                  {c.count}
                </span>
              </button>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-2 text-xs text-neutral-400 font-mono">
            <Filter className="w-3.5 h-3.5 text-[#FF7A18]" />
            <span>Showing {filteredBlueprints.length} of 10 flowcharts</span>
          </div>
        </div>
      </section>

      {/* Diagram Grid / Feed */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-12">
        {filteredBlueprints.map((item) => (
          <DiagramCard
            key={item.id}
            item={item}
            isMermaidReady={isMermaidReady}
          />
        ))}

        {/* Bottom CTA / Developer Links */}
        <section className="p-8 sm:p-12 rounded-3xl bg-gradient-to-r from-[#18181B] via-[#202024] to-[#18181B] border border-neutral-800 text-center space-y-5">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FF7A18]/10 border border-[#FF7A18]/30 text-xs font-mono font-bold text-[#FF7A18]">
            <Compass className="w-3.5 h-3.5" />
            <span>Developer Integration Suite</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-black text-white">
            Ready to Connect Your AI Agent?
          </h2>
          <p className="text-xs sm:text-sm text-neutral-400 max-w-xl mx-auto">
            Review the setup instructions for Claude Desktop (MCP), ChatGPT Custom GPT Actions, and
            Google Gemini Function Calling in our Developer Hub.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <Link href="/developer">
              <Button variant="primary" size="md" className="font-extrabold shadow-md">
                <span>View Integration Guides</span>
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
            <a
              href="https://github.com/Sahil9205/Transact-Ai/blob/main/docs/architecture_flowcharts.md"
              target="_blank"
              rel="noreferrer"
            >
              <Button variant="secondary" size="md" className="font-bold text-neutral-300 border-neutral-700 bg-neutral-800 hover:bg-neutral-700">
                <GitBranch className="w-4 h-4 mr-1 text-[#FF7A18]" />
                <span>GitHub Markdown Source</span>
              </Button>
            </a>
          </div>
        </section>
      </main>
    </div>
  );
}
