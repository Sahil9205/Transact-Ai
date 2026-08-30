#!/usr/bin/env python3
"""Transact AI — Interactive Terminal Commerce CLI.

Provides real-time interactive multi-turn commerce, agent discovery,
pre-flight gatekeeper verification, Razorpay test payment links, and audit timeline inspection.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import sys
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.config import get_settings
from app.db.database import init_database_manager
from app.db.seed import seed_database
from app.domain.schemas import BuyerIntentSchema
from app.services.agent_service import AgentService
from app.services.audit_service import AuditService
from app.services.discovery_service import DiscoveryService
from app.services.external_host_service import ExternalHostService
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.services.vector_service import get_vector_service

BANNER = r"""
  ╔══════════════════════════════════════════════════════════════════════╗
  ║    _____                           _          _    ___               ║
  ║   |_   _| __ __ _ _ __  ___  __ _  ___| |_       / \  |_ _|              ║
  ║     | || '__/ _` | '_ \/ __|/ _` |/ __| __|____ / _ \  | |               ║
  ║     | || | | (_| | | | \__ \ (_| | (__| ||_____/ ___ \ | |               ║
  ║     |_||_|  \__,_|_| |_|___/\__,_|\___|\__|   /_/   \_\___|              ║
  ║                                                                      ║
  ║     Autonomous Multi-Turn Agentic Commerce & Payment Engine          ║
  ╚══════════════════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
Commands:
  chat                - Start an interactive conversational commerce session
  search <query>      - Perform hybrid semantic search across all merchants
  orders              - View your order history and live delivery statuses
  timeline <order_id> - Inspect the 3-layer chronological audit trail
  tools [gemini|openai|anthropic] - View host-native tool schemas
  seed                - Re-seed database with multi-provider demo catalog
  help                - Show this help message
  exit / quit         - Exit Transact AI CLI
"""


async def run_interactive_chat(session: Any, user_id: str, vector_service: Any) -> None:
    """Runs a multi-turn interactive shopping session."""
    print("\n💬 [Transact AI Chat Mode] Type your request in English, Hindi, or Hinglish (e.g. '1kg Rasgulla in CP', 'Nescafe coffee powder').")
    print("   Type 'back' to return to the main menu.\n")

    while True:
        try:
            prompt = input("👤 You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not prompt or prompt.lower() in ["back", "exit"]:
            break

        print("\n🤖 Transact AI is thinking and searching providers...")
        final_state = await AgentService.run_agent(
            session=session,
            user_id=user_id,
            prompt=prompt,
            vector_service=vector_service,
        )

        print(f"\n{final_state['agent_message']}\n")

        # If an order proposal was created, offer 1-click confirmation & Razorpay payment
        proposal = final_state.get("order_proposal")
        if proposal and final_state.get("status") == "proposed":
            confirm = input("👉 Confirm order and generate payment link? (y/n): ").strip().lower()
            if confirm in ["y", "yes"]:
                print("\n💳 Initializing Razorpay test checkout order...")
                order_res = await PaymentService.create_payment_order(
                    session=session,
                    user_id=user_id,
                    product_id=proposal.product_id,
                    quantity=proposal.quantity,
                )

                print(f"✅ Order Created: {order_res.order_id}")
                print(f"💰 Amount: ₹{order_res.amount_inr:.2f} ({order_res.amount_paise} paise)")
                print(f"🔗 Payment Link: {order_res.payment_link_url}")

                # Simulate successful customer payment
                simulate = input("\n👉 Simulate instant test UPI/Card payment completion? (y/n): ").strip().lower()
                if simulate in ["y", "yes"]:
                    settings = get_settings()
                    mock_pay_id = f"pay_rzp_cli_{order_res.razorpay_order_id[-8:]}"
                    msg = f"{order_res.razorpay_order_id}|{mock_pay_id}".encode("utf-8")
                    sig = hmac.new(settings.RAZORPAY_KEY_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()

                    verify_res = await PaymentService.verify_payment_signature(
                        session=session,
                        razorpay_order_id=order_res.razorpay_order_id,
                        razorpay_payment_id=mock_pay_id,
                        razorpay_signature=sig,
                    )
                    print(f"🎉 {verify_res.message}")
                    print(f"📦 Final Status: {verify_res.status} | Order #{verify_res.order_id}\n")


async def main() -> None:
    """Main CLI entrypoint."""
    print(BANNER)
    settings = get_settings()
    db_manager = init_database_manager(settings.DATABASE_URL)
    await db_manager.init_db()

    vector_service = get_vector_service()
    try:
        await vector_service.ensure_collection()
    except Exception as e:
        pass

    user_id = "cli_shopper_1"

    async for session in db_manager.get_session():
        # Ensure database is seeded
        await seed_database(session, vector_service)

        print(HELP_TEXT)

        while True:
            try:
                cmd_line = input("Transact-AI> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break

            if not cmd_line:
                continue

            parts = cmd_line.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd in ["exit", "quit", "q"]:
                print("Goodbye!")
                break

            elif cmd == "help":
                print(HELP_TEXT)

            elif cmd == "chat":
                await run_interactive_chat(session, user_id, vector_service)

            elif cmd == "search":
                if not arg:
                    print("Usage: search <query> (e.g. 'search Rasgulla')")
                    continue
                intent = BuyerIntentSchema(product_query=arg)
                candidates = await DiscoveryService.match_candidates(session, intent, vector_service)
                if not candidates:
                    print(f"❌ No items found for '{arg}'.")
                else:
                    print(f"\n🔍 Found {len(candidates)} ranked options across providers:")
                    print("─" * 70)
                    for c in candidates:
                        print(f"#{c.rank} [{c.recommendation_tag}] {c.product.name}")
                        print(f"   🏪 Merchant: {c.merchant_name} ({c.merchant_type})")
                        print(f"   💰 Price: ₹{c.price_inr:.2f} | ⏱️ SLA: {c.fulfillment_sla} | Score: {c.score:.2f}")
                    print("─" * 70 + "\n")

            elif cmd == "orders":
                orders = await OrderService.list_user_orders(session, user_id)
                if not orders:
                    print("ℹ️ You have no previous orders.")
                else:
                    print(f"\n📦 Order History for {user_id}:")
                    print("─" * 70)
                    for o in orders:
                        print(f"• [{o.status.upper()}] Order #{o.order_id}")
                        print(f"  Item: {o.quantity}x {o.product_name} from {o.merchant_name} (₹{o.total_amount_inr:.2f})")
                        print(f"  Date: {o.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    print("─" * 70 + "\n")

            elif cmd == "timeline":
                if not arg:
                    print("Usage: timeline <order_id>")
                    continue
                timeline = await AuditService.get_order_timeline(session, arg)
                if not timeline.timeline:
                    print(f"❌ No audit events found for order '{arg}'.")
                else:
                    print(f"\n📜 3-Layer Chronological Audit Timeline for #{arg}:")
                    print("─" * 70)
                    for ev in timeline.timeline:
                        ts = ev.timestamp.strftime("%H:%M:%S")
                        res_badge = f"[{ev.result}] " if ev.result else ""
                        amt_badge = f"(₹{ev.amount_inr:.2f}) " if ev.amount_inr else ""
                        print(f"[{ts}] {ev.event_type.upper():<22} -> {res_badge}{amt_badge}{ev.reason or ''}")
                    print("─" * 70 + "\n")

            elif cmd == "tools":
                fmt = arg.strip().lower() if arg else "openai"
                tools = ExternalHostService.get_host_tools_schema(format=fmt)
                print(f"\n🤖 Exported {len(tools)} tools in '{fmt.upper()}' schema format:")
                for t in tools:
                    name = t.get("name") or t.get("function", {}).get("name")
                    desc = t.get("description") or t.get("function", {}).get("description")
                    print(f"• `{name}`: {desc}")
                print()

            elif cmd == "seed":
                print("🌱 Re-seeding database and Qdrant vector collection...")
                await seed_database(session, vector_service)
                print("✅ Seed completed.\n")

            else:
                print(f"Unknown command: '{cmd}'. Type 'help' for available commands.")

        break

    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
