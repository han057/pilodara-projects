# check_db3.py
# Verifies the unified sec_filings ChromaDB collection
# Shows total documents and breakdown by ticker

import chromadb

CHROMA_DIR  = "./data/chroma_db"
COLLECTION  = "sec_filings"

client = chromadb.PersistentClient(path=CHROMA_DIR)
cols   = client.list_collections()

print(f"Total collections: {len(cols)}")
for col in cols:
    print(f"  - {col.name}: {col.count()} documents")

# Show breakdown by ticker for sec_filings
try:
    col     = client.get_collection(COLLECTION)
    results = col.get(include=["metadatas"])
    metas   = results.get("metadatas", [])

    tickers = {}
    for m in metas:
        t = m.get("ticker", "UNKNOWN")
        tickers[t] = tickers.get(t, 0) + 1

    if tickers:
        print(f"\nBreakdown by ticker in '{COLLECTION}':")
        for ticker, count in sorted(tickers.items()):
            print(f"  {ticker}: {count} chunks")
except Exception as e:
    print(f"Could not read {COLLECTION}: {e}")
