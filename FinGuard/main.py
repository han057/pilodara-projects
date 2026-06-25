# main.py
# FastAPI endpoint — José
#
# Wraps the LangGraph multi-agent system in a REST API.
# Run with: python main.py
# Docs at:  http://localhost:8000/docs

import time
import uvicorn

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.graph import graph


# ---------------------------------------------------------------------------
# APP SETUP
# ---------------------------------------------------------------------------

app = FastAPI(
    title="FinGuard API",
    description=(
        "Multi-agent financial risk analysis system.\n\n"
        "Uses LangGraph orchestration with:\n"
        "- **Supervisor LLM** (qwen3:8b) — query reasoning and ticker extraction\n"
        "- **RAG Agent** (ChromaDB) — SEC filing retrieval (10-K / 10-Q)\n"
        "- **FMP Agent** (Financial Modeling Prep) — real-time market data\n"
        "- **Fundamental Analyst** — ratio interpretation and signal detection\n"
        "- **Risk Officer** — final structured risk assessment report"
    ),
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# REQUEST / RESPONSE MODELS
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        example="Analyze Tesla bankruptcy risk",
        description="Natural language financial query. Can reference one or multiple companies.",
    )


class AnalyzeResponse(BaseModel):
    query:      str
    tickers:    list[str]
    reasoning:  str
    report:     str
    latency_s:  float


# ---------------------------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def root():
    """Health check — confirms the API is running."""
    return {
        "status":  "ok",
        "service": "FinGuard API",
        "version": "1.0.0",
        "docs":    "http://localhost:8000/docs",
    }


@app.post("/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
def analyze(request: AnalyzeRequest):
    """
    Run a full multi-agent financial risk analysis.

    The system will:
    1. Use an LLM to identify companies and extract tickers
    2. Search SEC filings in ChromaDB (RAG)
    3. Fetch real-time data from FMP API
    4. Interpret ratios and generate risk signals
    5. Produce a structured Markdown risk assessment report

    **Example queries:**
    - `Analyze Tesla bankruptcy risk`
    - `Compare Tesla and Apple risk`
    - `Tell me about the iPhone company financial health`
    - `Is Nvidia a safe investment?`
    """
    t0 = time.time()

    try:
        result = graph.invoke({"query": request.query})
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent pipeline failed: {str(e)}"
        )

    return AnalyzeResponse(
        query     = request.query,
        tickers   = result.get("tickers", []),
        reasoning = result.get("supervisor_reasoning", ""),
        report    = result.get("final_report", "No report generated."),
        latency_s = round(time.time() - t0, 2),
    )


@app.get("/health", tags=["Health"])
def health():
    """Detailed health check with component status."""
    return {
        "status":     "ok",
        "components": {
            "langgraph":  "ready",
            "chromadb":   "./data/chroma_db",
            "ollama_url": "http://localhost:11434",
            "fmp_api":    "stable endpoints",
        }
    }


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
