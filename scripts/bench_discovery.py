"""Discovery & Orchestration Latency Benchmark for TransactAI.

Measures:
1. Query Embedding (Cold Inference vs Cached Lookup)
2. In-Memory Normalized Vector Cosine Similarity Search
3. Relational SQL Batch Product Metadata Queries
4. End-to-End Hybrid Discovery Pipeline (Vector + SQL)
5. Full 5-Node LangGraph State Machine Execution Loop

Saves raw metrics and system metadata to docs/benchmarks/discovery_benchmark_results.json.
"""

from __future__ import annotations

import asyncio
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.logging import setup_logging
from app.db.models import Base
from app.db.repository import ProductRepository
from app.db.seed import seed_database
from app.domain.enums import ProductCategory
from app.domain.schemas import BuyerIntentSchema
from app.services.agent_service import AgentService
from app.services.discovery_service import DiscoveryService
from app.services.policy_service import PolicyService
from app.services.vector_service import VectorService

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def get_git_commit() -> str:
    """Retrieve current Git commit hash."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def compute_stats(samples_ms: list[float]) -> dict[str, float]:
    """Compute min, mean, p50, p95, p99, max from millisecond timing samples."""
    arr = np.array(samples_ms, dtype=np.float64)
    return {
        "samples": len(samples_ms),
        "mean_ms": round(float(np.mean(arr)), 4),
        "min_ms": round(float(np.min(arr)), 4),
        "p50_ms": round(float(np.percentile(arr, 50)), 4),
        "p95_ms": round(float(np.percentile(arr, 95)), 4),
        "p99_ms": round(float(np.percentile(arr, 99)), 4),
        "max_ms": round(float(np.max(arr)), 4),
    }


async def run_benchmark(num_iterations: int = 100, warmup_runs: int = 10) -> dict[str, Any]:
    # Suppress debug/info logging during fast benchmarking
    setup_logging(log_level="WARNING", environment="production")

    print("=" * 70)
    print("TransactAI Latency & Throughput Benchmark")
    print("=" * 70)
    print(f"Python: {sys.version.split()[0]} | Platform: {platform.platform()}")
    print(f"Iterations: {num_iterations} (with {warmup_runs} warm-up runs)")
    print("-" * 70)

    # 1. Setup SQLite In-Memory Database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    # 2. Setup Vector Service with In-Memory Collection
    vector_service = VectorService(collection_name="bench_products")
    await vector_service.ensure_collection()

    # 3. Seed Catalog
    print("Seeding catalog...")
    async with session_maker() as session:
        await seed_database(session, vector_service)
        all_products = await ProductRepository.search(session, query="")
        product_count = len(all_products)
        sample_ids = [p.product_id for p in all_products[:5]]

    print(f"Catalog seeded with {product_count} products.")
    print("-" * 70)

    # Configure buyer policy for LangGraph loop
    test_user_id = "bench_user_42"
    async with session_maker() as session:
        await PolicyService.configure_policy(
            session=session,
            user_id=test_user_id,
            max_per_transaction_paise=100000,
            daily_limit_paise=500000,
        )

    # --- Benchmark 1: Query Embedding Inference (Cold vs Cached) ---
    print("1/5 Benchmarking Query Embedding...")
    cold_samples: list[float] = []
    # Test cold embedding generation on varying queries
    test_queries = [
        "fresh kaju katli sweets",
        "gulab jamun 1kg pack",
        "spicy samosa snack",
        "motichoor laddu festive box",
        "paneer butter masala gravy",
    ]
    for q in test_queries:
        t0 = time.perf_counter()
        _ = list(vector_service.embedder.embed([q]))
        t1 = time.perf_counter()
        cold_samples.append((t1 - t0) * 1000)

    # Warm cached queries
    warm_query = "fresh traditional rasgulla"
    # Pre-cache
    vector_service._get_query_embedding(warm_query)
    cached_samples: list[float] = []
    for _ in range(num_iterations):
        t0 = time.perf_counter()
        _ = vector_service._get_query_embedding(warm_query)
        t1 = time.perf_counter()
        cached_samples.append((t1 - t0) * 1000)

    # --- Benchmark 2: In-Memory Vector Similarity Match ---
    print("2/5 Benchmarking In-Memory Vector Cosine Search...")
    vec_samples: list[float] = []
    # Warmup
    for _ in range(warmup_runs):
        await vector_service.search_similar(query=warm_query, limit=5)

    for _ in range(num_iterations):
        t0 = time.perf_counter()
        # Direct tier-1 in-memory search
        _ = await vector_service.search_similar(query=warm_query, limit=5)
        t1 = time.perf_counter()
        vec_samples.append((t1 - t0) * 1000)

    # --- Benchmark 3: Relational SQL Product Batch Queries ---
    print("3/5 Benchmarking Relational SQL Metadata Queries...")
    sql_samples: list[float] = []
    async with session_maker() as session:
        for _ in range(warmup_runs):
            _ = await ProductRepository.get_by_product_ids(session, sample_ids)

        for _ in range(num_iterations):
            t0 = time.perf_counter()
            _ = await ProductRepository.get_by_product_ids(session, sample_ids)
            t1 = time.perf_counter()
            sql_samples.append((t1 - t0) * 1000)

    # --- Benchmark 4: End-to-End Hybrid Discovery Pipeline ---
    print("4/5 Benchmarking End-to-End Hybrid Discovery Pipeline...")
    discovery_intent = BuyerIntentSchema(
        product_query="Rasgulla sweets",
        max_price=500,
        category=ProductCategory.SWEETS,
        pincode="110001",
    )
    discovery_samples: list[float] = []
    async with session_maker() as session:
        for _ in range(warmup_runs):
            _ = await DiscoveryService.match_candidates(
                session=session,
                intent=discovery_intent,
                vector_service=vector_service,
            )

        for _ in range(num_iterations):
            t0 = time.perf_counter()
            _ = await DiscoveryService.match_candidates(
                session=session,
                intent=discovery_intent,
                vector_service=vector_service,
            )
            t1 = time.perf_counter()
            discovery_samples.append((t1 - t0) * 1000)

    # --- Benchmark 5: Full 5-Node LangGraph Agent Execution Loop ---
    print("5/5 Benchmarking Full 5-Node LangGraph Agent Workflow...")
    agent_prompt = "1kg Traditional Rasgulla chahiye under Rs 500 in 110001"
    agent_samples: list[float] = []
    async with session_maker() as session:
        for _ in range(warmup_runs):
            _ = await AgentService.run_agent(
                session=session,
                user_id=test_user_id,
                prompt=agent_prompt,
                vector_service=vector_service,
            )

        for _ in range(num_iterations):
            t0 = time.perf_counter()
            _ = await AgentService.run_agent(
                session=session,
                user_id=test_user_id,
                prompt=agent_prompt,
                vector_service=vector_service,
            )
            t1 = time.perf_counter()
            agent_samples.append((t1 - t0) * 1000)

    await engine.dispose()

    # Compile Final Report
    report = {
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "git_commit": get_git_commit(),
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "processor": platform.processor() or "Unknown",
            "dataset_size_products": product_count,
            "iterations": num_iterations,
            "warmup_runs": warmup_runs,
        },
        "benchmarks": {
            "embedding_cold_inference": compute_stats(cold_samples),
            "embedding_cache_hit": compute_stats(cached_samples),
            "vector_cosine_similarity": compute_stats(vec_samples),
            "relational_sql_batch_query": compute_stats(sql_samples),
            "hybrid_discovery_pipeline": compute_stats(discovery_samples),
            "full_langgraph_agent_loop": compute_stats(agent_samples),
        },
    }

    # Print Summary Table
    print("\n" + "=" * 80)
    print(f"{'Benchmark Component':<38} | {'Mean (ms)':<10} | {'P50 (ms)':<10} | {'P95 (ms)':<10} | {'P99 (ms)':<10}")
    print("-" * 80)
    for name, stats in report["benchmarks"].items():
        print(f"{name:<38} | {stats['mean_ms']:<10.3f} | {stats['p50_ms']:<10.3f} | {stats['p95_ms']:<10.3f} | {stats['p99_ms']:<10.3f}")
    print("=" * 80)

    # Save to docs/benchmarks/
    out_dir = Path("docs/benchmarks")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "discovery_benchmark_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved raw benchmark output to: {out_file}")

    return report


if __name__ == "__main__":
    asyncio.run(run_benchmark(num_iterations=100, warmup_runs=10))
