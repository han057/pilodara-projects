# indexar.py
# Document indexing script — Natalia
#
# Indexes SEC EDGAR filings (10-K / 10-Q) into ChromaDB.
# Supports both PDF and HTML formats (SEC EDGAR inline viewer format).
#
# Usage:
#   1. Place SEC filing files inside the ./docs/ folder
#      - HTML files: download the "ix.html" from the _files subfolder
#      - PDF files: place directly in ./docs/
#   2. Run: python indexar.py
#   3. ChromaDB will be created at ./data/chroma_db/
#
# Collection naming convention: {TICKER}-COLLECTION
# e.g. Tesla files → TSLA-COLLECTION

import os
import re
from pathlib import Path

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredHTMLLoader, PyPDFLoader


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

EMBED_MODEL  = "nomic-embed-text"
OLLAMA_URL   = "http://localhost:11434"
PERSIST_DIR  = "./data/chroma_db"
DOCS_FOLDER  = Path("./docs")
CHUNK_SIZE   = 1000
CHUNK_OVERLAP = 150


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _clean_collection_name(raw: str) -> str:
    """
    ChromaDB collection names must be 3-63 chars,
    containing only letters, digits, hyphens, underscores, or dots.
    """
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "", raw)
    if len(cleaned) < 3:
        cleaned = "DOC-COLLECTION"
    return f"{cleaned}-COLLECTION"


def _detect_ticker(filename: str) -> str:
    """
    Attempts to extract the ticker from the filename.
    Falls back to 'UNKNOWN' if not recognisable.
    """
    name_upper = filename.upper()
    known = {
        "TESLA": "TSLA",
        "TSLA":  "TSLA",
        "APPLE": "AAPL",
        "AAPL":  "AAPL",
        "NVIDIA":"NVDA",
        "NVDA":  "NVDA",
        "MSFT":  "MSFT",
        "AMZN":  "AMZN",
    }
    for keyword, ticker in known.items():
        if keyword in name_upper:
            return ticker
    return "UNKNOWN"


def _detect_doc_type(filename: str) -> str:
    name_upper = filename.upper()
    if "10-K" in name_upper:
        return "10-K"
    if "10-Q" in name_upper:
        return "10-Q"
    return "SEC-FILING"


# ---------------------------------------------------------------------------
# MAIN INDEXING FUNCTION
# ---------------------------------------------------------------------------

def index_documents():
    print("=" * 60)
    print("FinGuard — SEC Document Indexing Pipeline")
    print("=" * 60)
    print()

    print(f"Initializing embedding model: {EMBED_MODEL}")
    embeddings = OllamaEmbeddings(
        model=EMBED_MODEL,
        base_url=OLLAMA_URL,
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    # Search for ix.html inside SEC EDGAR _files subfolders (primary)
    # and any .pdf or .html files directly in docs/ (fallback)
    target_files = (
        list(DOCS_FOLDER.rglob("ix.html")) +
        list(DOCS_FOLDER.glob("*.pdf")) +
        list(DOCS_FOLDER.glob("*.html"))
    )

    # Deduplicate
    target_files = list(dict.fromkeys(target_files))

    if not target_files:
        print(f"ERROR: No documents found in {DOCS_FOLDER}/")
        print("  Place SEC EDGAR HTML or PDF files inside ./docs/")
        return

    print(f"Found {len(target_files)} document(s) to index.")
    print()

    for filepath in target_files:
        print(f"Processing: {filepath}")

        # Detect ticker and document type from parent folder or filename
        source_name = filepath.parent.name if filepath.name == "ix.html" else filepath.name
        ticker      = _detect_ticker(source_name)
        doc_type    = _detect_doc_type(source_name)

        # Choose loader based on file type
        suffix = filepath.suffix.lower()
        if suffix in [".html", ".htm"]:
            loader = UnstructuredHTMLLoader(str(filepath))
        elif suffix == ".pdf":
            loader = PyPDFLoader(str(filepath))
        else:
            print(f"  Skipping unsupported file type: {suffix}")
            continue

        try:
            pages = loader.load()
        except Exception as e:
            print(f"  ERROR loading file: {e}")
            continue

        chunks = splitter.split_documents(pages)
        print(f"  Chunks generated : {len(chunks)}")

        if len(chunks) == 0:
            print(f"  WARNING: No text extracted. Skipping.")
            continue

        # Add metadata to each chunk for filtering during retrieval
        for chunk in chunks:
            chunk.metadata["source"]   = source_name
            chunk.metadata["ticker"]   = ticker
            chunk.metadata["doc_type"] = doc_type

        collection_name = f"{ticker}-COLLECTION"
        print(f"  Saving to ChromaDB collection: {collection_name}")

        store = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=PERSIST_DIR,
        )

        ids = [f"{ticker}_{doc_type}_{i}" for i in range(len(chunks))]
        store.add_documents(chunks, ids=ids)

        print(f"  Done. {len(chunks)} chunks saved to {collection_name}.")
        print()

    print("=" * 60)
    print(f"Indexing complete. ChromaDB saved to {PERSIST_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    index_documents()
