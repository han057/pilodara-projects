# sec_agent.py
# Dynamic SEC EDGAR Agent for FinGuard
#
# Given a ticker (e.g. "NVDA"), this module:
#   1. Resolves the ticker to its CIK via SEC EDGAR
#   2. Checks if already indexed in sec_filings collection (cache)
#   3. If not, downloads the latest 10-K and indexes it
#   4. Uses direct ollama client for embeddings (fixes Windows port issues)
#
# All data stored in: ./data/chroma_db  collection: sec_filings
# Search with filter={"ticker": "NVDA"} at query time.
#
# Usage:
#   from sec_agent import ensure_company_indexed
#   result = ensure_company_indexed("NVDA")
#
# Manual run:
#   python sec_agent.py

import json
import time
import warnings
from pathlib import Path

import chromadb
import ollama
import requests
from langchain_community.document_loaders import PyPDFLoader, UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from bs4 import XMLParsedAsHTMLWarning
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
except ImportError:
    pass


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": "FinGuard Project nataliastekolnikova2025@gmail.com"
}

DOCS_DIR          = Path("./docs")
CHROMA_DIR        = Path("./data/chroma_db")
COLLECTION_NAME   = "sec_filings"
TICKER_CACHE_FILE = Path("./sec_tickers_cache.json")

DOCS_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

EMBED_MODEL   = "nomic-embed-text"
CHUNK_SIZE    = 800
CHUNK_OVERLAP = 100

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)

# Direct ollama client — bypasses langchain proxy issues on Windows
_ollama_client = ollama.Client(host="http://127.0.0.1:11434")

# ChromaDB client — direct, no langchain wrapper needed for indexing
_chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))


# ---------------------------------------------------------------------------
# CHROMADB HELPERS
# ---------------------------------------------------------------------------

def _get_collection() -> chromadb.Collection:
    """Returns (or creates) the unified sec_filings collection."""
    return _chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _already_indexed(ticker: str) -> bool:
    """Checks if ticker has documents in sec_filings."""
    try:
        col     = _get_collection()
        results = col.get(where={"ticker": ticker.upper()}, limit=1)
        return len(results.get("ids", [])) > 0
    except Exception:
        return False


def _embed(texts: list[str]) -> list[list[float]]:
    """
    Generates embeddings using direct ollama client.
    Processes in batches of 50 to avoid memory issues with large documents.
    """
    all_vectors = []
    batch_size  = 50

    for i in range(0, len(texts), batch_size):
        batch    = texts[i:i + batch_size]
        response = _ollama_client.embed(model=EMBED_MODEL, input=batch)
        all_vectors.extend(response.embeddings)

    return all_vectors


# ---------------------------------------------------------------------------
# STEP 1 — Resolve ticker to CIK
# ---------------------------------------------------------------------------

def _load_ticker_map() -> dict:
    """Downloads (or uses 24h local cache of) the SEC ticker to CIK map."""
    if TICKER_CACHE_FILE.exists():
        age_hours = (time.time() - TICKER_CACHE_FILE.stat().st_mtime) / 3600
        if age_hours < 24:
            return json.loads(TICKER_CACHE_FILE.read_text(encoding="utf-8"))

    print("   [SEC] Downloading ticker map from SEC EDGAR...")
    url  = "https://www.sec.gov/files/company_tickers.json"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    ticker_map = {
        item["ticker"].upper(): str(item["cik_str"]).zfill(10)
        for item in data.values()
    }

    TICKER_CACHE_FILE.write_text(json.dumps(ticker_map), encoding="utf-8")
    print(f"   [SEC] Ticker map cached ({len(ticker_map)} entries).")
    return ticker_map


def get_cik(ticker: str) -> str | None:
    """Returns the 10-digit CIK for a ticker, or None if not found."""
    return _load_ticker_map().get(ticker.upper())


# ---------------------------------------------------------------------------
# STEP 2 — Find latest 10-K on EDGAR
# ---------------------------------------------------------------------------

def get_latest_10k_url(cik: str) -> dict | None:
    """Finds the most recent 10-K filing for a given CIK."""
    url  = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data   = resp.json()
    recent = data["filings"]["recent"]

    for i, form in enumerate(recent["form"]):
        if form in ("10-K", "10-K/A"):
            accession_raw    = recent["accessionNumber"][i]
            accession_nodash = accession_raw.replace("-", "")
            primary_doc      = recent["primaryDocument"][i]
            filing_date      = recent["filingDate"][i]

            doc_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{int(cik)}/{accession_nodash}/{primary_doc}"
            )
            return {
                "url":             doc_url,
                "form":            form,
                "filingDate":      filing_date,
                "accessionNumber": accession_raw,
            }
    return None


# ---------------------------------------------------------------------------
# STEP 3 — Download filing
# ---------------------------------------------------------------------------

def _download_filing(ticker: str, filing_info: dict) -> Path:
    """Downloads the 10-K and saves to ./docs/{TICKER}_10K.{ext}"""
    print(f"   [SEC] Downloading {filing_info['form']} ({filing_info['filingDate']})...")
    resp = requests.get(filing_info["url"], headers=HEADERS, timeout=60)
    resp.raise_for_status()

    url_lower = filing_info["url"].lower()
    ext       = ".htm" if url_lower.endswith((".htm", ".html")) else ".pdf"
    out_path  = DOCS_DIR / f"{ticker.upper()}_10K{ext}"
    out_path.write_bytes(resp.content)

    size_kb = out_path.stat().st_size // 1024
    print(f"   [SEC] Saved to {out_path} ({size_kb} KB)")
    return out_path


# ---------------------------------------------------------------------------
# STEP 4 — Index into ChromaDB using direct ollama client
# ---------------------------------------------------------------------------

def _index_filing(ticker: str, file_path: Path, filing_info: dict) -> int:
    """
    Loads, splits and indexes a filing into the unified sec_filings collection.
    Uses direct ollama client for embeddings — avoids Windows port issues.
    """
    print(f"   [SEC] Loading {file_path.name}...")

    suffix = file_path.suffix.lower()
    loader = PyPDFLoader(str(file_path)) if suffix == ".pdf" else UnstructuredHTMLLoader(str(file_path))

    pages  = loader.load()
    chunks = splitter.split_documents(pages)

    if not chunks:
        print(f"   [SEC] WARNING: No text extracted from {file_path.name}.")
        return 0

    print(f"   [SEC] Generating embeddings for {len(chunks)} chunks...")

    # Enrich metadata
    filing_year = filing_info["filingDate"][:4]
    texts, metas, ids = [], [], []

    for i, chunk in enumerate(chunks):
        chunk.metadata["ticker"]     = ticker.upper()
        chunk.metadata["source"]     = file_path.name
        chunk.metadata["form"]       = filing_info["form"]
        chunk.metadata["filingDate"] = filing_info["filingDate"]
        chunk.metadata["year"]       = filing_year

        texts.append(chunk.page_content)
        metas.append(chunk.metadata)
        ids.append(f"{ticker.upper()}_{filing_year}_{i}")

    # Generate embeddings via direct ollama client
    vectors = _embed(texts)

    # Store in ChromaDB
    col = _get_collection()
    col.add(
        ids        = ids,
        embeddings = vectors,
        documents  = texts,
        metadatas  = metas,
    )

    print(f"   [SEC] Indexed {len(chunks)} chunks into {COLLECTION_NAME} (ticker={ticker.upper()}).")
    return len(chunks)


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def ensure_company_indexed(ticker: str, force: bool = False) -> dict:
    """
    Ensures the latest 10-K for a ticker is indexed in sec_filings.

    Args:
        ticker: stock symbol, e.g. "NVDA", "TSLA", "AAPL"
        force:  if True, re-downloads and re-indexes even if cached

    Returns:
        dict with keys: ticker, status, chunks_added, filingDate, form, file
    """
    ticker = ticker.upper()

    if not force and _already_indexed(ticker):
        col   = _get_collection()
        count = len(col.get(where={"ticker": ticker}, include=[])["ids"])
        print(f"   [SEC] {ticker} already in sec_filings ({count} chunks). Using cache.")
        return {
            "ticker":       ticker,
            "status":       "cached",
            "chunks_added": 0,
        }

    cik = get_cik(ticker)
    if cik is None:
        return {
            "ticker":  ticker,
            "status":  "error",
            "message": f"{ticker} not found in SEC EDGAR.",
        }

    print(f"   [SEC] CIK for {ticker}: {cik}")

    filing_info = get_latest_10k_url(cik)
    if filing_info is None:
        return {
            "ticker":  ticker,
            "status":  "error",
            "message": f"No recent 10-K found for {ticker}.",
        }

    file_path = _download_filing(ticker, filing_info)
    n_chunks  = _index_filing(ticker, file_path, filing_info)

    return {
        "ticker":       ticker,
        "status":       "indexed",
        "chunks_added": n_chunks,
        "filingDate":   filing_info["filingDate"],
        "form":         filing_info["form"],
        "file":         str(file_path),
    }


def query_company(ticker: str, question: str, k: int = 4) -> list:
    """Searches sec_filings for relevant fragments for a specific ticker."""
    col     = _get_collection()
    vectors = _embed([question])

    results = col.query(
        query_embeddings = vectors,
        n_results        = k,
        where            = {"ticker": ticker.upper()},
        include          = ["documents", "metadatas"],
    )

    return results.get("documents", [[]])[0]


# ---------------------------------------------------------------------------
# MANUAL RUN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("FinGuard — SEC EDGAR Auto-Indexing Agent")
    print(f"Collection: {COLLECTION_NAME} in {CHROMA_DIR}")
    print("=" * 60)

    companies = ["META", "EPAM"]

    for ticker in companies:
        print(f"\n{'─' * 40}")
        print(f"Processing: {ticker}")
        result = ensure_company_indexed(ticker)
        print(f"Result: {result}")

        if result["status"] in ("cached", "indexed"):
            docs = query_company(ticker, "What are the main risk factors?", k=2)
            print(f"Test query: {len(docs)} fragments found.")
            if docs:
                print(f"Preview: {docs[0][:200]}...")

    print("\n" + "=" * 60)
    print("Done. Run check_db3.py to verify.")
    print("=" * 60)
