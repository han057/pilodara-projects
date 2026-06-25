# app/agents/rag_agent.py
# RAG Retriever Agent for FinGuard
#
# Architecture: single collection 'sec_filings' with ticker metadata filter.
# Uses direct ollama client for embeddings — fixes Windows port issues.
# Search with filter={"ticker": "TSLA"} at query time.

import chromadb
import ollama
from pathlib import Path

from app.config import OLLAMA_HOST, EMBED_MODEL, CHROMA_PATH, COLLECTION_NAME
_CHROMA_PATH  = CHROMA_PATH
_COLLECTION   = COLLECTION_NAME
_EMBED_MODEL  = EMBED_MODEL
_TOP_K        = 4

# Direct clients — bypass langchain wrapper issues on Windows
_ollama_client = ollama.Client(host=OLLAMA_HOST)
_chroma_client = chromadb.PersistentClient(path=_CHROMA_PATH)


def _get_collection() -> chromadb.Collection:
    """Returns the unified sec_filings collection."""
    return _chroma_client.get_or_create_collection(
        name=_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def _embed(text: str) -> list[float]:
    """Generates embedding for a single query string."""
    response = _ollama_client.embed(model=_EMBED_MODEL, input=[text])
    return response.embeddings[0]


def _ticker_indexed(ticker: str) -> bool:
    """Checks if ticker has documents in sec_filings."""
    try:
        col     = _get_collection()
        results = col.get(where={"ticker": ticker.upper()}, limit=1)
        return len(results.get("ids", [])) > 0
    except Exception:
        return False


def retrieve(ticker: str, query: str) -> dict:
    """
    Main retrieval function called by the RAG agent node.

    Strategy:
      1. Check if ticker exists in sec_filings collection
      2. If not — auto-download from SEC EDGAR via sec_agent.py
      3. Run similarity search with ticker metadata filter
      4. Return structured result for downstream agents

    Args:
        ticker: stock ticker symbol (e.g. "TSLA")
        query:  user query for semantic similarity search

    Returns:
        dict with keys: ticker, texto, fuente, found
    """
    # Step 1: check if ticker is indexed
    if not _ticker_indexed(ticker):
        print(f"   [RAG] {ticker} not in sec_filings. Fetching from SEC EDGAR...")
        try:
            from sec_agent import ensure_company_indexed
            result = ensure_company_indexed(ticker)
            print(f"   [RAG] SEC EDGAR: {result['status']} — {result.get('chunks_added', 0)} chunks added.")
        except Exception as e:
            print(f"   [RAG] SEC EDGAR indexing failed: {e}")
            return {
                "ticker": ticker,
                "texto":  f"No SEC filings available for {ticker}.",
                "fuente": f"ChromaDB — sec_filings (no data for {ticker})",
                "found":  False,
            }

    # Step 2: generate query embedding
    try:
        vector = _embed(query)
    except Exception as e:
        print(f"   [RAG] Embedding failed: {e}")
        return {
            "ticker": ticker,
            "texto":  "Embedding generation failed.",
            "fuente": "ChromaDB — sec_filings (error)",
            "found":  False,
        }

    # Step 3: similarity search with ticker filter
    try:
        col     = _get_collection()
        results = col.query(
            query_embeddings = [vector],
            n_results        = _TOP_K,
            where            = {"ticker": ticker.upper()},
            include          = ["documents", "metadatas"],
        )

        docs  = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

    except Exception as e:
        print(f"   [RAG] Similarity search failed for {ticker}: {e}")
        return {
            "ticker": ticker,
            "texto":  "Search failed.",
            "fuente": "ChromaDB — sec_filings (error)",
            "found":  False,
        }

    if not docs:
        return {
            "ticker": ticker,
            "texto":  f"No relevant fragments found for query: '{query}'",
            "fuente": f"ChromaDB — sec_filings ({ticker})",
            "found":  False,
        }

    fragments = "\n\n---\n\n".join(docs)
    source    = metas[0].get("source", ticker) if metas else ticker
    form      = metas[0].get("form", "10-K") if metas else "10-K"
    date      = metas[0].get("filingDate", "") if metas else ""

    print(f"   [RAG] Retrieved {len(docs)} fragments from {source} ({form} {date})")

    return {
        "ticker": ticker,
        "texto":  fragments,
        "fuente": f"ChromaDB — sec_filings | {ticker} | {form} {date}",
        "found":  True,
    }
