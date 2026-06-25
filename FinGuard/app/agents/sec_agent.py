"""
sec_agent.py
-------------
Dynamic SEC EDGAR agent for FinGuard.

Given a ticker (e.g. "NVDA"), this module:
  1. Resolves the ticker to its CIK (Central Index Key) in SEC EDGAR.
  2. Checks whether it is already indexed in ChromaDB (cache).
  3. If not, downloads the latest 10-K, indexes it, and stores it.
  4. Returns the relevant chunks ready to use in the RAG pipeline.

Usage:
    from sec_agent import ensure_company_indexed

    result = ensure_company_indexed("NVDA")
"""

import json
import time
from pathlib import Path

import requests
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# -----------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------

# The SEC REQUIRES an identifiable User-Agent with a real contact email.
HEADERS = {"User-Agent": "FinGuard Project nataliastekolnikova2025@gmail.com"}

DOCS_DIR = Path("./docs")
CHROMA_DIR = Path("./chroma_db")
TICKER_CACHE_FILE = Path("./sec_tickers_cache.json")

DOCS_DIR.mkdir(exist_ok=True)

embeddings = OllamaEmbeddings(model="nomic-embed-text")
splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)

store = Chroma(
    collection_name="empresas_sec",
    embedding_function=embeddings,
    persist_directory=str(CHROMA_DIR),
)


# -----------------------------------------------------------------
# Step 1 — Resolve ticker -> CIK
# -----------------------------------------------------------------

def _load_ticker_map() -> dict:
    """Downloads (or uses local cache of) the full SEC ticker -> CIK map."""
    if TICKER_CACHE_FILE.exists():
        # Cache valid for 24h to avoid hitting the API unnecessarily
        age_hours = (time.time() - TICKER_CACHE_FILE.stat().st_mtime) / 3600
        if age_hours < 24:
            return json.loads(TICKER_CACHE_FILE.read_text(encoding="utf-8"))

    url = "https://www.sec.gov/files/company_tickers.json"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # Normalize to {ticker: cik_10_digits}
    ticker_map = {}
    for item in data.values():
        ticker_map[item["ticker"].upper()] = str(item["cik_str"]).zfill(10)

    TICKER_CACHE_FILE.write_text(json.dumps(ticker_map), encoding="utf-8")
    return ticker_map


def get_cik(ticker: str) -> str | None:
    """Returns the 10-digit CIK for a ticker, or None if not found."""
    ticker_map = _load_ticker_map()
    return ticker_map.get(ticker.upper())


# -----------------------------------------------------------------
# Step 2 — Find the latest 10-K on EDGAR
# -----------------------------------------------------------------

def get_latest_10k_url(cik: str) -> dict | None:
    """
    Returns a dict with info about the latest 10-K:
        {"url": ..., "form": "10-K", "filingDate": ..., "accessionNumber": ...}
    or None if none is found.
    """
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    recent = data["filings"]["recent"]
    forms = recent["form"]

    for i, form in enumerate(forms):
        if form in ("10-K", "10-K/A"):
            accession_raw = recent["accessionNumber"][i]
            accession_nodash = accession_raw.replace("-", "")
            primary_doc = recent["primaryDocument"][i]
            filing_date = recent["filingDate"][i]

            doc_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{int(cik)}/{accession_nodash}/{primary_doc}"
            )
            return {
                "url": doc_url,
                "form": form,
                "filingDate": filing_date,
                "accessionNumber": accession_raw,
            }
    return None


# -----------------------------------------------------------------
# Step 3 — Check if already indexed (Chroma cache)
# -----------------------------------------------------------------

def _already_indexed(ticker: str) -> bool:
    """Checks whether chunks for this ticker already exist in the collection."""
    try:
        existing = store.get(where={"ticker": ticker.upper()}, limit=1)
        return len(existing.get("ids", [])) > 0
    except Exception:
        return False


# -----------------------------------------------------------------
# Step 4 — Download, save, and index
# -----------------------------------------------------------------

def _download_filing(ticker: str, filing_info: dict) -> Path:
    """Downloads the filing document and saves it to ./docs/<TICKER>_10K.<ext>"""
    resp = requests.get(filing_info["url"], headers=HEADERS, timeout=30)
    resp.raise_for_status()

    # Most modern 10-Ks are HTML, not pure PDF.
    ext = ".htm" if filing_info["url"].lower().endswith((".htm", ".html")) else ".pdf"
    out_path = DOCS_DIR / f"{ticker.upper()}_10K{ext}"
    out_path.write_bytes(resp.content)
    return out_path


def _index_filing(ticker: str, file_path: Path, filing_info: dict) -> int:
    """Indexes the downloaded filing into ChromaDB with enriched metadata."""
    if file_path.suffix.lower() == ".pdf":
        loader = PyPDFLoader(str(file_path))
        pages = loader.load()
    else:
        # Simple fallback for HTML: load as plain text via BeautifulSoup.
        from langchain_community.document_loaders import BSHTMLLoader
        loader = BSHTMLLoader(str(file_path), open_encoding="utf-8")
        pages = loader.load()

    chunks = splitter.split_documents(pages)

    for c in chunks:
        c.metadata["ticker"] = ticker.upper()
        c.metadata["source"] = file_path.name
        c.metadata["form"] = filing_info["form"]
        c.metadata["filingDate"] = filing_info["filingDate"]

    ids = [f"{ticker.upper()}_{i}" for i in range(len(chunks))]
    store.add_documents(chunks, ids=ids)
    return len(chunks)


# -----------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------

def ensure_company_indexed(ticker: str, force: bool = False) -> dict:
    """
    Ensures that the latest 10-K for `ticker` is indexed in ChromaDB.

    Args:
        ticker: stock symbol, e.g. "NVDA", "TSLA", "AAPL".
        force: if True, re-downloads and re-indexes even if it already exists.

    Returns:
        dict describing the result of the operation.
    """
    ticker = ticker.upper()

    if not force and _already_indexed(ticker):
        return {"ticker": ticker, "status": "cached", "chunks_added": 0}

    cik = get_cik(ticker)
    if cik is None:
        return {"ticker": ticker, "status": "error", "message": "Ticker not found in SEC EDGAR"}

    filing_info = get_latest_10k_url(cik)
    if filing_info is None:
        return {"ticker": ticker, "status": "error", "message": "No recent 10-K found"}

    file_path = _download_filing(ticker, filing_info)
    n_chunks = _index_filing(ticker, file_path, filing_info)

    return {
        "ticker": ticker,
        "status": "indexed",
        "chunks_added": n_chunks,
        "filingDate": filing_info["filingDate"],
        "form": filing_info["form"],
        "file": str(file_path),
    }


def query_company(ticker: str, question: str, k: int = 4):
    """Searches for relevant fragments for an already-indexed company."""
    return store.similarity_search(
        question,
        k=k,
        filter={"ticker": ticker.upper()},
    )


# -----------------------------------------------------------------
# Manual demo
# -----------------------------------------------------------------

if __name__ == "__main__":
    for t in ["NVDA", "MSFT", "AMZN"]:
        print(f"\n--- Processing {t} ---")
        result = ensure_company_indexed(t)
        print(result)

        if result["status"] in ("cached", "indexed"):
            docs = query_company(t, "What are the main risk factors?")
            print(f"  Found {len(docs)} relevant fragments.")
            if docs:
                print(f"  Example: {docs[0].page_content[:200]}...")
