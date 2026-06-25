# FinGuard 🛡️
### Multi-Agent Financial Risk Analysis System

> Final project — AI Agents & RAG course

FinGuard analyzes the financial health of publicly traded companies using real SEC EDGAR filings (10-K / 10-Q) and live market data from the FMP API, then generates a structured risk assessment report.

---

## How it works

```
User: "Analyze Tesla bankruptcy risk"
              ↓
     Supervisor Agent (qwen3:8b)
     Reasons about query → extracts tickers
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
RAG Retriever       FMP Analyst
ChromaDB search     FMP API calls
SEC 10-K / 10-Q     Price, ratios,
auto-indexed        Altman Z-Score
    ↓                   ↓
    └─────────┬─────────┘
              ↓
   Fundamental Analyst
   Interprets ratios + signals
              ↓
       Risk Officer
  Final report + verdict
```

---

## Agent architecture

| Agent | Role | Tech |
|---|---|---|
| **Supervisor** | Reasons about query, extracts tickers, routes to agents | qwen3:8b via Ollama |
| **RAG Retriever** | Searches SEC filings in ChromaDB, auto-indexes new companies | ChromaDB + nomic-embed-text |
| **FMP Analyst** | Fetches real-time price, ratios, calculates Altman Z-Score | FMP API (stable endpoints) |
| **Fundamental Analyst** | Interprets each ratio, generates risk signals | Rule-based |
| **Risk Officer** | Consolidates all data, generates final Markdown report | LangGraph END node |

---

## Tech stack

| Component | Tool |
|---|---|
| Agent orchestration | LangGraph |
| Local LLM | qwen3:8b via Ollama |
| Embeddings | nomic-embed-text via Ollama |
| Vector store | ChromaDB (single `sec_filings` collection) |
| Real-time data | FMP API (stable endpoints, free plan) |
| SEC filings | SEC EDGAR (auto-downloaded 10-K) |
| API layer | FastAPI + Uvicorn |

---

## Pre-indexed companies

The following companies are ready to query out of the box:

| Ticker | Company | 10-K Date | Chunks |
|---|---|---|---|
| TSLA | Tesla, Inc. | 2026-04-30 | 261 |
| AAPL | Apple Inc. | 2025-10-31 | 311 |
| NVDA | NVIDIA Corporation | 2026-02-25 | 462 |
| MSFT | Microsoft Corporation | 2025-07-30 | 400 |
| AMZN | Amazon.com, Inc. | 2026-02-06 | 308 |
| META | Meta Platforms, Inc. | 2026-01-29 | 691 |
| GOOGL | Alphabet Inc. | 2026-02-05 | 401 |
| EPAM | EPAM Systems, Inc. | 2026-02-26 | 454 |

Any other publicly traded company on SEC EDGAR is indexed automatically on first query.

---

## Setup

### Prerequisites

- Python 3.12
- [Ollama](https://ollama.com) installed

### 1. Clone the repository

```bash
git clone https://github.com/NataliaStekolnikova/finguard.git
cd finguard
```

### 2. Create virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / Mac
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Create the `.env` file using Python (important — do NOT use `echo` on Windows as it creates wrong encoding):

```bash
python -c "open('.env', 'w', encoding='utf-8').write('FMP_API_KEY=your_api_key_here\n')"
```

Register for a free FMP API key at [financialmodelingprep.com/register](https://financialmodelingprep.com/register)
Free plan: **250 requests/day** — sufficient for testing and demo.

> ⚠️ **Never commit `.env` to git.** It is already in `.gitignore`.
> ⚠️ **Windows users:** always create `.env` with Python, not with `echo` — Windows CMD/PowerShell saves files in UTF-16 encoding which Python cannot read correctly.

### 5. Pull Ollama models

```bash
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

### 6. Start Ollama

```bash
ollama serve
```
### 7. Index SEC filings

On first run, download and index the pre-configured companies into ChromaDB:

```bash
python sec_agent.py
```

This downloads the latest 10-K from SEC EDGAR for:
TSLA, AAPL, NVDA, MSFT, AMZN, META, GOOGL, EPAM

Takes 10-15 minutes on first run. Subsequent runs are instant (cached).

> **Note:** The ChromaDB database is not included in the repository (see `.gitignore`).
> You must run this script after cloning. Any company not in the list is indexed
> automatically on first query.


### 8. Run the system

**Console mode:**
```bash
python test_local.py
```

**API mode:**
```bash
python main.py
# Open http://localhost:8000/docs
```

---

## Example queries

```
Analyze Tesla bankruptcy risk
Compare Tesla and Apple risk
Is Nvidia a safe investment?
Tell me about the iPhone company financial health
Dime cual es el nivel de riesgo de Meta
Compare Microsoft and Amazon risk
```

The Supervisor LLM understands natural language in any language and indirect company references ("iPhone company" → AAPL, "Windows company" → MSFT).

---

## Example output

```
## 📋 FINANCIAL RISK ASSESSMENT — TSLA

**Verdict:** LOW RISK ✅ (Safe Zone)
**Assessment:** Altman Z-Score confirms very low bankruptcy probability.

**SEC Filing Context:**
> Tesla 10-K 2026: The company reports stable operating cash flow...
**Source:** ChromaDB — sec_filings | TSLA | 10-K 2026-04-30

| Metric          | Value    | Source              |
| :---            | :---:    | :---                |
| Stock Price     | $400.49  | FMP API             |
| P/E Ratio       | 381.12x  | FMP API             |
| Debt / Equity   | 0.10     | FMP API             |
| Quick Ratio     | 1.77     | FMP API             |
| ROE             | 0.0462   | FMP API             |
| Revenue Growth  | -2.9%    | FMP API             |
| Altman Z-Score  | 17.35    | Calculated (FMP)    |

**Signal breakdown:**
- Altman Z-Score 17.35 → Safe zone (bankruptcy probability < 1%)
- P/E 381.1x → extreme growth premium, high valuation risk
- Debt/Equity 0.10 → very conservative leverage
- Revenue growth -2.9% YoY → slight decline, watch trend
- Quick ratio 1.77 → adequate liquidity
```

---

## Data sources

### FMP API (real-time)
- Stock prices, P/E, Debt/Equity, ROE, ROA, Gross Margin
- Income statement, balance sheet, cash flow
- Free plan: **250 requests/day**
- Register at [financialmodelingprep.com](https://financialmodelingprep.com/register)

### SEC EDGAR (historical)
- Annual reports 10-K (auto-downloaded on first query)
- Indexed in ChromaDB — single `sec_filings` collection
- Fully **free and public**

---

## Project structure

```
finguard/
├── main.py                      ← FastAPI server
├── test_local.py                ← interactive console
├── indexar.py                   ← manual indexing script
├── sec_agent.py                 ← auto SEC EDGAR indexer
├── app/
│   ├── graph.py                 ← LangGraph topology (nodes + edges only)
│   ├── state.py                 ← shared agent state (TypedDict)
│   └── agents/
│       ├── supervisor_agent.py  ← ReAct LLM routing
│       ├── rag_agent.py         ← ChromaDB retrieval
│       ├── fmp_agent.py         ← FMP API integration
│       ├── fundamental_agent.py ← ratio interpretation
│       └── risk_officer.py      ← report generation
├── data/chroma_db/              ← vector store (git-ignored)
├── docs/                        ← downloaded SEC filings (git-ignored)
├── .env.example                 ← environment template
└── requirements.txt
```

---

## Academic requirements

| Requirement | Implementation |
|---|---|
| Multi-agent system | 5 specialized agents + Supervisor via LangGraph |
| RAG + vector store | SEC filings in ChromaDB `sec_filings` collection |
| Document indexing | 10-K auto-downloaded from SEC EDGAR per company |
| Public API | FMP API with real-time financial data |
| Realistic demo | Any public company analyzed in real time |

---

## Environment variables

```bash
# .env
FMP_API_KEY=your_api_key_here
```

**Never commit `.env` to git.** It is listed in `.gitignore`.
