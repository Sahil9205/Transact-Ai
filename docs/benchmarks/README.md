# TransactAI Latency & Throughput Benchmark

This benchmark evaluates the latency profile of TransactAI across five critical sub-systems:
1. **Query Embedding**: Cold model inference (`BAAI/bge-small-en-v1.5` via FastEmbed) vs. warm in-memory LRU cache hit.
2. **In-Memory Vector Search**: Normalized cosine dot product across the catalog candidates.
3. **Relational SQL Queries**: Batch metadata hydration via SQLAlchemy Async + SQLite.
4. **Hybrid Discovery Pipeline**: Combined concurrent vector search, database query, candidate scoring, and ranking.
5. **Full LangGraph Workflow Loop**: End-to-end 5-node autonomous agent graph execution (`parse_intent` $\rightarrow$ `discover_candidates` $\rightarrow$ `verify_and_gatekeep` $\rightarrow$ `create_proposal`).

---

## Benchmark Results

Raw JSON results are saved in [`discovery_benchmark_results.json`](discovery_benchmark_results.json).

| Pipeline Component | Metric Tested | P50 (ms) | P95 (ms) | P99 (ms) | Mean (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Embedding (Cold)** | FastEmbed 384-dim ONNX inference | **163.74 ms** | 176.91 ms | 177.93 ms | 165.59 ms |
| **Embedding (Cached)** | In-memory LRU cache retrieval | **0.001 ms** | 0.001 ms | 0.003 ms | 0.001 ms |
| **Vector Similarity** | Tier-1 in-memory cosine dot product | **0.20 ms** | 0.36 ms | 0.52 ms | 0.24 ms |
| **Relational SQL Batch** | SQLAlchemy batch lookup (`WHERE IN`) | **6.80 ms** | 7.57 ms | 7.81 ms | 6.75 ms |
| **Hybrid Discovery** | End-to-end parallel search + rank | **14.37 ms** | 15.69 ms | 18.38 ms | 14.33 ms |
| **Full LangGraph Loop** | 5-node deterministic agent state graph | **88.11 ms** | 120.31 ms | 127.45 ms | 91.95 ms |

---

## Environment Specification

- **Script**: `scripts/bench_discovery.py`
- **Dataset**: 49 products across 6 seeded merchants
- **Iterations**: 100 measured iterations (preceded by 10 warm-up runs)
- **Runtime**: Python 3.12, Windows 11, AMD64
