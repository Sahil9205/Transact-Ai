"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  Code,
  Terminal,
  Cpu,
  Layers,
  Sparkles,
  ExternalLink,
  Copy,
  CheckCircle2,
  ShieldCheck,
  Search,
  BookOpen,
  ArrowRight,
  Database,
  Lock,
  Bot,
  Zap,
  Check,
  FileCode,
  Globe,
  Sliders,
  Store,
  ChevronRight,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import PatternDivider from "@/components/patterns/PatternDivider";
import MandalaAccent from "@/components/patterns/MandalaAccent";
import { useToast } from "@/components/ui/Toast";

type AssistantType = "claude" | "chatgpt" | "gemini";

interface GuideStep {
  step: number;
  title: string;
  desc: string;
  details?: string[];
  promptExample?: string;
}

interface AssistantGuide {
  id: AssistantType;
  name: string;
  provider: string;
  tag: string;
  color: string;
  bgLight: string;
  badgeBg: string;
  description: string;
  configFilePath: {
    windows: string;
    mac: string;
  };
  configCode: string;
  steps: GuideStep[];
  toolTrace: {
    call: string;
    policy: string;
    result: string;
  };
}

const DEFAULT_FRONTEND_URL = "https://frontend-six-steel-85.vercel.app";
const DEFAULT_BACKEND_URL = "https://transact-ai-production.up.railway.app";

function getAssistantGuides(frontendUrl: string, backendUrl: string): Record<AssistantType, AssistantGuide> {
  const fe = frontendUrl.replace(/\/+$/, "");
  const be = backendUrl.replace(/\/+$/, "");

  return {
    claude: {
      id: "claude",
      name: "Claude Desktop",
      provider: "Anthropic MCP",
      tag: "Native Model Context Protocol",
      color: "#D97706",
      bgLight: "bg-amber-50 border-amber-200 text-amber-900",
      badgeBg: "bg-[#FFF4E6] border-[#FFD9A8] text-[#FF7A18]",
      description:
        "AI decides. TransactAI transacts. Connect Claude Desktop directly to TransactAI's MCP execution engine. Claude acts as the conversational reasoning and comparison layer, while TransactAI provides deterministic catalog verification, spending guardrails, and Razorpay checkout settlements.",
      configFilePath: {
        windows: `%APPDATA%\\Claude\\claude_desktop_config.json`,
        mac: `~/Library/Application Support/Claude/claude_desktop_config.json`,
      },
      configCode: `{
  "mcpServers": {
    "transactai": {
      "command": "python",
      "args": [
        "-m",
        "app.mcp.server"
      ],
      "env": {
        "TRANSACTAI_BASE_URL": "${fe}"
      }
    }
  }
}`,
      steps: [
        {
          step: 1,
          title: "Locate Your Claude Desktop Config File",
          desc: "Open your Claude Desktop configuration file on your machine:",
          details: [
            "Windows: Win+R → %APPDATA%\\Claude\\claude_desktop_config.json",
            "macOS: ~/Library/Application Support/Claude/claude_desktop_config.json",
          ],
        },
        {
          step: 2,
          title: "Add TransactAI MCP Server Definition",
          desc: `Paste the JSON configuration below into your mcpServers block. Notice TRANSACTAI_BASE_URL points to your live hosted frontend (${fe}) so checkout links work seamlessly.`,
        },
        {
          step: 3,
          title: "Restart Claude Desktop",
          desc: "Completely quit Claude Desktop (check system tray) and reopen it. You will see a small hammer/tools icon indicating TransactAI tools are active.",
        },
        {
          step: 4,
          title: "Test with a Real Prompt",
          desc: "Ask Claude in natural language:",
          promptExample:
            "Search for fresh Kaju Katli in Indiranagar (pincode 560001) under ₹600. Verify my daily spending policy limit, and if approved, prepare an order summary for my confirmation.",
        },
      ],
      toolTrace: {
        call: `transact_search_catalog({"query": "kaju katli", "pincode": "560001", "max_price_inr": 600})`,
        policy: `transact_check_policy({"user_id": "buyer-1", "amount_paise": 45000}) -> ALLOWED`,
        result: `Order initialized. Payment checkout link: ${fe}/pay/ord_9f82ab...`,
      },
    },

    chatgpt: {
      id: "chatgpt",
      name: "ChatGPT",
      provider: "OpenAI Custom GPTs & Actions",
      tag: "OpenAPI Actions Integration",
      color: "#10A37F",
      bgLight: "bg-emerald-50 border-emerald-200 text-emerald-900",
      badgeBg: "bg-emerald-50 border-emerald-300 text-emerald-800",
      description:
        "AI decides. TransactAI transacts. Connect ChatGPT using OpenAI Custom GPT Actions. ChatGPT handles product research, price/quality evaluation, and user decision-making, while TransactAI enforces stock parity, spending policies, and checkout execution.",
      configFilePath: {
        windows: "ChatGPT Web Interface > Explore GPTs > Create a GPT > Actions",
        mac: "ChatGPT Web Interface > Explore GPTs > Create a GPT > Actions",
      },
      configCode: `${be}/.well-known/openapi.json`,
      steps: [
        {
          step: 1,
          title: "Open ChatGPT Custom GPT Builder",
          desc: "In ChatGPT Plus/Team/Enterprise, click 'Explore GPTs' in the sidebar, then click '+ Create' to open the GPT editor.",
        },
        {
          step: 2,
          title: "Create a New Action via OpenAPI URL",
          desc: "Go to the 'Configure' tab, scroll down to 'Actions', and click 'Create new action'. Click 'Import from URL' and enter:",
          details: [
            `Import URL: ${be}/.well-known/openapi.json`,
            `Or via Frontend Proxy: ${fe}/.well-known/openapi.json`,
          ],
        },
        {
          step: 3,
          title: "Add Agent Guardrail Instructions",
          desc: "In the Instructions box, paste this production execution protocol:",
          promptExample:
            "You are ChatGPT connected to TransactAI, an AI Commerce Execution Agent. Help users research and compare products. Only trigger TransactAI when the user expresses clear purchase intent ('Buy this', 'Place order'). Validate stock, enforce spending policy limits, never silently replace unavailable items, and always get explicit user confirmation before generating the payment link.",
        },
        {
          step: 4,
          title: "Test Your Custom GPT",
          desc: "In the Preview pane, prompt your GPT:",
          promptExample:
            "Order 1kg Alphonso mangoes to pincode 560001. Check if it's within my ₹1,000 budget and ask for my confirmation before ordering.",
        },
      ],
      toolTrace: {
        call: `POST /api/v1/discovery/search {"query": "alphonso mangoes", "pincode": "560001"}`,
        policy: `POST /api/v1/policies/validate {"user_id": "buyer-1", "amount_paise": 35000} -> ALLOWED`,
        result: `Order created. Payment link generated: ${fe}/pay/ord_mango_332`,
      },
    },

    gemini: {
      id: "gemini",
      name: "Google Gemini",
      provider: "Gemini Extensions & GenAI SDK",
      tag: "Gemini Function Calling SDK",
      color: "#2563EB",
      bgLight: "bg-blue-50 border-blue-200 text-blue-900",
      badgeBg: "bg-blue-50 border-blue-300 text-blue-800",
      description:
        "Connect Google Gemini models using Google Generative AI Python/TS SDK function calling or the TransactAI Gemini Extension manifest at /.well-known/gemini-extension.json.",
      configFilePath: {
        windows: `${be}/.well-known/gemini-extension.json`,
        mac: `${be}/.well-known/gemini-extension.json`,
      },
      configCode: `import google.generativeai as genai
import requests

# 1. Fetch TransactAI Gemini tool declarations from live backend
manifest = requests.get("${be}/.well-known/gemini-extension.json").json()

# 2. Configure Gemini 1.5 Pro with TransactAI tools
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    tools=[
        {
            "function_declarations": [
                {
                    "name": "transact_search_catalog",
                    "description": "Search local verified merchant catalogs",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "query": {"type": "STRING"},
                            "pincode": {"type": "STRING"}
                        },
                        "required": ["query"]
                    }
                }
            ]
        }
    ]
)

# 3. Prompt Gemini
chat = model.start_chat(enable_automatic_function_calling=True)
response = chat.send_message("Find 1 liter farm fresh milk near 560001 and initiate purchase.")
print(response.text)`,
      steps: [
        {
          step: 1,
          title: "Access the Gemini Extension Manifest",
          desc: "TransactAI serves an official Gemini extension manifest at:",
          details: [
            `Manifest URL: ${be}/.well-known/gemini-extension.json`,
          ],
        },
        {
          step: 2,
          title: "Integrate with Google GenAI SDK",
          desc: "Use the Python or Node.js @google/genai SDK with function declarations pointing to TransactAI's live production endpoints.",
        },
        {
          step: 3,
          title: "Run the Automated Commerce Chat Loop",
          desc: "Enable enable_automatic_function_calling=True. Gemini will automatically invoke TransactAI's endpoints when a user requests grocery or food items.",
        },
        {
          step: 4,
          title: "Verify Execution in Console",
          desc: "Watch the merchant dashboard update in real-time as Gemini fulfills the user request.",
        },
      ],
      toolTrace: {
        call: `Gemini FunctionCall: transact_search_catalog(query='milk', pincode='560001')`,
        policy: `Policy Validation: ₹65 within daily limit ₹3,000`,
        result: `Settlement link generated via Razorpay webhook on ${fe}/pay/ord_... Status: Ready for pickup.`,
      },
    },
  };
}

const MCP_TOOLS = [
  {
    name: "transact_search_catalog",
    method: "POST",
    endpoint: "/api/v1/discovery/search",
    description:
      "Performs high-dimensional semantic vector search across local merchant catalogs via Qdrant.",
    parameters: [
      { name: "query", type: "string", required: true, desc: "Natural language query e.g. 'fresh cow milk'" },
      { name: "pincode", type: "string", required: false, desc: "Target 6-digit delivery pincode" },
      { name: "category", type: "string", required: false, desc: "Filtered product category" },
      { name: "max_price_inr", type: "number", required: false, desc: "Price ceiling in INR" },
    ],
  },
  {
    name: "transact_check_policy",
    method: "POST",
    endpoint: "/api/v1/policies/validate",
    description:
      "Deterministic pre-transaction check ensuring user daily limit and single-order limits are respected.",
    parameters: [
      { name: "user_id", type: "string", required: true, desc: "Buyer identifier" },
      { name: "amount_paise", type: "integer", required: true, desc: "Order value in paise" },
      { name: "category", type: "string", required: true, desc: "Item category" },
    ],
  },
  {
    name: "transact_create_payment_order",
    method: "POST",
    endpoint: "/api/v1/payments/create-order",
    description:
      "Initializes a Razorpay order in test mode from confirmed proposal and generates hosted checkout link.",
    parameters: [
      { name: "user_id", type: "string", required: true, desc: "Target user ID" },
      { name: "product_id", type: "string", required: true, desc: "UUID of product" },
      { name: "quantity", type: "integer", required: true, desc: "Quantity of items" },
      { name: "pincode", type: "string", required: false, desc: "Delivery destination PIN" },
    ],
  },
  {
    name: "transact_verify_payment",
    method: "POST",
    endpoint: "/api/v1/payments/verify-signature",
    description:
      "Validates cryptographic HMAC-SHA256 payment signature from client checkout.",
    parameters: [
      { name: "razorpay_order_id", type: "string", required: true, desc: "Razorpay order ID" },
      { name: "razorpay_payment_id", type: "string", required: true, desc: "Razorpay transaction ID" },
      { name: "razorpay_signature", type: "string", required: true, desc: "Cryptographic HMAC-SHA256 signature" },
    ],
  },
];

export default function DeveloperPage() {
  const { showToast } = useToast();
  const [activeAssistant, setActiveAssistant] = useState<AssistantType>("claude");
  const [copied, setCopied] = useState(false);
  const [frontendUrl, setFrontendUrl] = useState(DEFAULT_FRONTEND_URL);
  const [backendUrl, setBackendUrl] = useState(DEFAULT_BACKEND_URL);

  useEffect(() => {
    if (typeof window !== "undefined" && window.location.origin) {
      setFrontendUrl(window.location.origin);
    }
  }, []);

  const guides = useMemo(
    () => getAssistantGuides(frontendUrl, backendUrl),
    [frontendUrl, backendUrl]
  );
  const guide = guides[activeAssistant];

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    showToast("Configuration copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-[#FFF9F2] text-[#171717] pb-24">
      {/* Hero Section */}
      <section className="relative pt-16 pb-12 overflow-hidden border-b border-[#F0DED0] bg-white">
        <MandalaAccent className="absolute -top-24 -right-24 w-96 h-96 text-[#FF7A18] opacity-[0.25] pointer-events-none" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="max-w-3xl space-y-4">
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#FFF4E6] border border-[#FFD9A8] text-xs font-bold text-[#FF7A18] uppercase tracking-wider">
              <Terminal className="w-3.5 h-3.5" />
              <span>Developer Portal • Connect Your AI Assistant</span>
            </div>
            <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-[#171717]">
              Connect Claude, ChatGPT &amp; Gemini to Real-World Commerce
            </h1>
            <p className="text-sm sm:text-base text-[#5F5F5F] leading-relaxed">
              Equip your AI assistant with standard tools to search local merchant catalogs, enforce mathematical spending guardrails, and execute Razorpay settlements with zero hallucinations.
            </p>

            {/* Live Endpoint Status Pill */}
            <div className="flex flex-wrap items-center gap-2.5 pt-1 text-xs font-mono">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 shadow-2xs">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[#6B7280]">Backend API:</span>
                <span className="font-semibold text-emerald-900">{backendUrl}</span>
              </div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#FFF4E6] border border-[#FFD9A8] text-[#171717] shadow-2xs">
                <span className="w-2 h-2 rounded-full bg-[#FF7A18]" />
                <span className="text-[#8A8A8A]">Hosted Checkout:</span>
                <span className="font-semibold text-[#171717]">{frontendUrl}</span>
              </div>
            </div>

            {/* Prominent 3 Connection Selectors */}
            <div className="pt-3">
              <p className="text-xs font-bold text-[#8A8A8A] uppercase tracking-wider mb-2.5">
                Choose your AI Assistant to connect:
              </p>
              <div className="flex flex-wrap gap-3">
                {/* Claude Button */}
                <button
                  type="button"
                  onClick={() => setActiveAssistant("claude")}
                  className={`inline-flex items-center gap-2.5 px-4 py-3 rounded-2xl border text-xs sm:text-sm font-extrabold transition-all cursor-pointer shadow-xs ${
                    activeAssistant === "claude"
                      ? "bg-[#D97706] text-white border-[#B45309] shadow-md scale-102"
                      : "bg-[#FFF4E6] text-[#171717] border-[#FFD9A8] hover:bg-[#FFE8C7]"
                  }`}
                >
                  <Bot className="w-4 h-4" />
                  <span>Connect Claude (MCP)</span>
                  {activeAssistant === "claude" && <Check className="w-4 h-4 ml-1" />}
                </button>

                {/* ChatGPT Button */}
                <button
                  type="button"
                  onClick={() => setActiveAssistant("chatgpt")}
                  className={`inline-flex items-center gap-2.5 px-4 py-3 rounded-2xl border text-xs sm:text-sm font-extrabold transition-all cursor-pointer shadow-xs ${
                    activeAssistant === "chatgpt"
                      ? "bg-[#10A37F] text-white border-[#059669] shadow-md scale-102"
                      : "bg-[#FFF4E6] text-[#171717] border-[#FFD9A8] hover:bg-[#FFE8C7]"
                  }`}
                >
                  <Sparkles className="w-4 h-4" />
                  <span>Connect ChatGPT (Actions)</span>
                  {activeAssistant === "chatgpt" && <Check className="w-4 h-4 ml-1" />}
                </button>

                {/* Gemini Button */}
                <button
                  type="button"
                  onClick={() => setActiveAssistant("gemini")}
                  className={`inline-flex items-center gap-2.5 px-4 py-3 rounded-2xl border text-xs sm:text-sm font-extrabold transition-all cursor-pointer shadow-xs ${
                    activeAssistant === "gemini"
                      ? "bg-[#2563EB] text-white border-[#1D4ED8] shadow-md scale-102"
                      : "bg-[#FFF4E6] text-[#171717] border-[#FFD9A8] hover:bg-[#FFE8C7]"
                  }`}
                >
                  <Cpu className="w-4 h-4" />
                  <span>Connect Gemini (SDK/Ext)</span>
                  {activeAssistant === "gemini" && <Check className="w-4 h-4 ml-1" />}
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Interactive Guide */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 space-y-14">
        {/* Dynamic Detailed Connection Guide for Selected Assistant */}
        <section className="bg-white rounded-3xl border border-[#F0DED0] p-6 sm:p-10 shadow-sm space-y-8 animate-in fade-in duration-200">
          {/* Header Lockup */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#F0DED0]">
            <div className="space-y-1">
              <div className="flex items-center gap-2.5">
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-extrabold border ${guide.badgeBg}`}>
                  {guide.tag}
                </span>
                <span className="text-xs text-[#5F5F5F] font-bold">{guide.provider}</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-black text-[#171717] tracking-tight">
                How to Connect {guide.name} to TransactAI
              </h2>
              <p className="text-xs sm:text-sm text-[#5F5F5F] max-w-2xl">{guide.description}</p>
            </div>

            <button
              onClick={() => handleCopy(guide.configCode)}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#FFF4E6] hover:bg-[#FFE8C7] border border-[#FFD9A8] text-xs font-extrabold text-[#171717] transition-all cursor-pointer shadow-2xs self-start sm:self-center"
            >
              {copied ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Copied to Clipboard!</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4 text-[#FF7A18]" />
                  <span>Copy Configuration</span>
                </>
              )}
            </button>
          </div>

          {/* Steps & Code Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Step-by-Step Instructions (7 cols) */}
            <div className="lg:col-span-7 space-y-6">
              <h3 className="text-base font-extrabold text-[#171717] flex items-center gap-2">
                <Sliders className="w-4 h-4 text-[#FF203D]" />
                <span>Step-by-Step Setup Guide</span>
              </h3>

              <div className="space-y-4">
                {guide.steps.map((s) => (
                  <div
                    key={s.step}
                    className="p-4 rounded-2xl bg-[#FFF9F2] border border-[#F0DED0] space-y-2 relative"
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="w-6 h-6 rounded-full bg-[#FFF4E6] border border-[#FFD9A8] text-[#FF203D] font-mono font-black text-xs flex items-center justify-center">
                        {s.step}
                      </span>
                      <h4 className="font-extrabold text-sm text-[#171717]">{s.title}</h4>
                    </div>

                    <p className="text-xs text-[#5F5F5F] leading-relaxed pl-8.5">{s.desc}</p>

                    {s.details && (
                      <div className="pl-8.5 pt-1 space-y-1 text-[11px] font-mono text-[#171717]">
                        {s.details.map((d, i) => (
                          <div key={i} className="bg-white p-2 rounded-lg border border-[#F0DED0]">
                            {d}
                          </div>
                        ))}
                      </div>
                    )}

                    {s.promptExample && (
                      <div className="pl-8.5 pt-1">
                        <div className="p-3 bg-white rounded-xl border border-[#FFD9A8] text-xs font-semibold text-[#171717] flex items-start gap-2">
                          <Sparkles className="w-3.5 h-3.5 text-[#FF7A18] shrink-0 mt-0.5" />
                          <span>&ldquo;{s.promptExample}&rdquo;</span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Code Configuration Box (5 cols) */}
            <div className="lg:col-span-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-extrabold text-[#171717] flex items-center gap-2">
                  <FileCode className="w-4 h-4 text-[#FF7A18]" />
                  <span>Configuration Snippet</span>
                </h3>
                <span className="text-[11px] font-bold text-[#8A8A8A] font-mono">JSON / Code</span>
              </div>

              <div className="rounded-2xl bg-[#171717] text-[#FFF9F2] p-4 font-mono text-xs overflow-x-auto shadow-xl border border-neutral-800 leading-relaxed max-h-[380px] overflow-y-auto">
                <pre className="selection:bg-[#FF203D] selection:text-white">
                  <code>{guide.configCode}</code>
                </pre>
              </div>

              {/* Real-time Tool Execution Trace Box */}
              <div className="p-4 rounded-2xl bg-[#FFF4E6] border border-[#FFD9A8] space-y-2">
                <div className="text-xs font-bold text-[#171717] flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5 text-[#FF7A18]" />
                  <span>Under the Hood Execution Flow</span>
                </div>
                <div className="space-y-1.5 font-mono text-[11px] text-[#5F5F5F]">
                  <div className="bg-white p-2 rounded-lg border border-[#F0DED0]">
                    <span className="text-[#FF7A18] font-bold">1. AI Tool Call:</span>
                    <div className="text-[#171717] truncate">{guide.toolTrace.call}</div>
                  </div>
                  <div className="bg-white p-2 rounded-lg border border-[#F0DED0]">
                    <span className="text-emerald-700 font-bold">2. Guardrail Check:</span>
                    <div className="text-[#171717]">{guide.toolTrace.policy}</div>
                  </div>
                  <div className="bg-white p-2 rounded-lg border border-[#F0DED0]">
                    <span className="text-[#FF203D] font-bold">3. Checkout Generation:</span>
                    <div className="text-[#171717]">{guide.toolTrace.result}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* MCP Standard Tools Breakdown */}
        <section className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-2xl font-black text-[#171717] tracking-tight flex items-center gap-2.5">
                <Cpu className="w-6 h-6 text-[#FF203D]" />
                <span>Registered Model Context Protocol (MCP) Tools</span>
              </h2>
              <p className="text-xs sm:text-sm text-[#5F5F5F] mt-1">
                These are the exact tools exposed to your AI assistants to safely interact with real inventory and payment gateways.
              </p>
            </div>

            {/* Subtle secondary specs links */}
            <div className="flex items-center gap-2 text-xs font-bold text-[#5F5F5F]">
              <a
                href="/.well-known/openapi.json"
                target="_blank"
                rel="noreferrer"
                className="hover:text-[#FF203D] flex items-center gap-1 transition-colors"
              >
                <span>Raw OpenAPI JSON</span>
                <ExternalLink className="w-3 h-3" />
              </a>
              <span>•</span>
              <a
                href="/docs"
                target="_blank"
                rel="noreferrer"
                className="hover:text-[#FF203D] flex items-center gap-1 transition-colors"
              >
                <span>Swagger UI</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {MCP_TOOLS.map((tool) => (
              <div
                key={tool.name}
                className="bg-white rounded-3xl p-6 border border-[#F0DED0] shadow-sm space-y-4 hover:border-[#FFD9A8] transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="font-mono font-extrabold text-sm text-[#FF203D]">
                    {tool.name}
                  </div>
                  <span className="px-2 py-0.5 rounded-md font-mono text-[10px] font-bold bg-[#FFF4E6] border border-[#FFD9A8] text-[#FF7A18]">
                    {tool.method}
                  </span>
                </div>

                <p className="text-xs text-[#5F5F5F] leading-relaxed">{tool.description}</p>

                <div className="space-y-2 pt-2 border-t border-[#F0DED0]">
                  <div className="text-[11px] font-bold text-[#8A8A8A] uppercase tracking-wider">
                    Parameters
                  </div>
                  <div className="space-y-1.5">
                    {tool.parameters.map((param) => (
                      <div
                        key={param.name}
                        className="text-xs flex flex-col sm:flex-row sm:items-baseline justify-between p-2 rounded-xl bg-[#FFF9F2] border border-[#F0DED0]"
                      >
                        <div className="font-mono font-bold text-[#171717]">
                          {param.name}{" "}
                          <span className="text-[10px] text-[#8A8A8A] font-normal">
                            ({param.type})
                          </span>
                          {param.required && (
                            <span className="text-[10px] text-[#FF203D] font-bold ml-1">
                              *
                            </span>
                          )}
                        </div>
                        <span className="text-[11px] text-[#5F5F5F] mt-0.5 sm:mt-0">
                          {param.desc}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
