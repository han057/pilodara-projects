# evaluation.py
# Automated quality evaluation for FinGuard
#
# Tests the correctness of:
#   1. Supervisor LLM — ticker extraction and routing
#   2. RAG Retriever — ChromaDB document retrieval
#
# Run with: python evaluation.py
# All tests must pass before the final demo.

import time
from app.agents.supervisor_agent import run_supervisor
from app.agents.rag_agent import retrieve


# ---------------------------------------------------------------------------
# TEST HELPERS
# ---------------------------------------------------------------------------

PASS = "✅ PASS"
FAIL = "❌ FAIL"

results = []


def test(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    results.append((name, condition, detail))
    print(f"  {status}  {name}")
    if detail:
        print(f"         {detail}")


# ---------------------------------------------------------------------------
# SUPERVISOR TESTS
# ---------------------------------------------------------------------------

def run_supervisor_tests():
    print("\n" + "=" * 60)
    print("SUPERVISOR AGENT TESTS")
    print("=" * 60)

    # Test 1: Direct ticker extraction
    print("\n[Test 1] Direct company name → ticker")
    t0 = time.time()
    result = run_supervisor("Analyze Tesla bankruptcy risk")
    latency = round(time.time() - t0, 1)
    tickers = result.get("tickers", [])
    test(
        "Tesla → TSLA",
        "TSLA" in tickers,
        f"Got: {tickers} | Latency: {latency}s"
    )

    # Test 2: Indirect reference
    print("\n[Test 2] Indirect company reference → ticker")
    result = run_supervisor("Tell me about the iPhone company financial health")
    tickers = result.get("tickers", [])
    test(
        "'iPhone company' → AAPL",
        "AAPL" in tickers,
        f"Got: {tickers}"
    )

    # Test 3: Non-English query
    print("\n[Test 3] Spanish language query → ticker")
    result = run_supervisor("Dime cual es el nivel de riesgo de Meta")
    tickers = result.get("tickers", [])
    test(
        "Spanish query → META",
        "META" in tickers,
        f"Got: {tickers}"
    )

    # Test 4: Comparison mode — two tickers
    print("\n[Test 4] Comparison query → two tickers")
    result = run_supervisor("Compare Tesla and Apple risk")
    tickers = result.get("tickers", [])
    comparison = result.get("comparison_mode", False)
    test(
        "Two tickers extracted",
        "TSLA" in tickers and "AAPL" in tickers,
        f"Got: {tickers}"
    )
    test(
        "Comparison mode detected",
        comparison is True,
        f"comparison_mode: {comparison}"
    )

    # Test 5: Nvidia indirect reference
    print("\n[Test 5] 'GPU chip company' → NVDA")
    result = run_supervisor("Is the GPU chip company a safe investment?")
    tickers = result.get("tickers", [])
    test(
        "'GPU chip company' → NVDA",
        "NVDA" in tickers,
        f"Got: {tickers}"
    )


# ---------------------------------------------------------------------------
# RAG RETRIEVAL TESTS
# ---------------------------------------------------------------------------

def run_rag_tests():
    print("\n" + "=" * 60)
    print("RAG RETRIEVAL TESTS")
    print("=" * 60)

    # Test 6: Tesla — should be in ChromaDB
    print("\n[Test 6] Tesla RAG retrieval")
    result = retrieve("TSLA", "bankruptcy risk debt liquidity")
    test(
        "TSLA found in ChromaDB",
        result["found"] is True,
        f"Source: {result.get('fuente', 'N/A')}"
    )
    test(
        "TSLA context not empty",
        len(result.get("texto", "")) > 100,
        f"Text length: {len(result.get('texto', ''))} chars"
    )

    # Test 7: Apple — should be in ChromaDB
    print("\n[Test 7] Apple RAG retrieval")
    result = retrieve("AAPL", "revenue growth financial risk")
    test(
        "AAPL found in ChromaDB",
        result["found"] is True,
        f"Source: {result.get('fuente', 'N/A')}"
    )

    # Test 8: Nvidia — should be in ChromaDB
    print("\n[Test 8] Nvidia RAG retrieval")
    result = retrieve("NVDA", "risk factors semiconductor")
    test(
        "NVDA found in ChromaDB",
        result["found"] is True,
        f"Source: {result.get('fuente', 'N/A')}"
    )

    # Test 9: Metadata check — source should reference sec_filings
    print("\n[Test 9] RAG source metadata")
    result = retrieve("MSFT", "cloud revenue growth")
    fuente = result.get("fuente", "")
    test(
        "Source references sec_filings collection",
        "sec_filings" in fuente,
        f"Source: {fuente}"
    )

    # Test 10: Context relevance — should contain financial terms
    print("\n[Test 10] RAG context relevance")
    result = retrieve("AMZN", "revenue operating income cash flow")
    texto = result.get("texto", "").lower()
    financial_terms = ["amazon", "annual", "report", "form", "item", "sec", "business", "operations"]
    found_terms = [t for t in financial_terms if t in texto]
    test(
    "Context is from SEC filing document",
    len(found_terms) >= 2,
    f"Terms found: {found_terms}"
    )



# ---------------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------------

def print_summary():
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, ok, _ in results if ok)
    total  = len(results)
    pct    = round(passed / total * 100)

    for name, ok, detail in results:
        status = "✅" if ok else "❌"
        print(f"  {status}  {name}")

    print(f"\nResult: {passed}/{total} tests passed ({pct}%)")

    if passed == total:
        print("\n🎉 All tests passed. System is ready for demo.")
    elif passed >= total * 0.8:
        print("\n⚠️  Most tests passed. Review failures before demo.")
    else:
        print("\n❌  Too many failures. System needs attention.")

    return passed == total


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("FinGuard — Automated Evaluation")
    print("Testing Supervisor LLM and RAG Retriever...")

    run_supervisor_tests()
    run_rag_tests()
    success = print_summary()

    exit(0 if success else 1)
