# app/state.py
# Shared state definition for the LangGraph multi-agent system
#
# FinancialState is the single source of truth passed between all agents.
# Each agent reads what it needs and writes only its own outputs.
#
# Design principle: immutable inputs, append-only lists for parallel agents.

from typing import TypedDict, Optional, List


class FinancialState(TypedDict):
    # --- Input ---
    query: str                          # original user question

    # --- Supervisor decisions ---
    tickers: List[str]                  # e.g. ["TSLA"] or ["TSLA", "AAPL"]
    current_agent: str                  # for logging/debugging
    supervisor_reasoning: str           # LLM chain-of-thought

    # --- RAG Agent output (Natalia) ---
    # One dict per ticker: {ticker, texto, fuente, found}
    rag_results: List[dict]

    # --- FMP Agent output (Oksana) ---
    # One dict per ticker: {ticker, current_price, pe_ratio, ...}
    fmp_results: List[dict]

    # --- Fundamental Analyst output (Oksana) ---
    # One dict per ticker: {ticker, signals, summary, risk_level}
    analyses: List[dict]

    # --- Risk Officer output (José) ---
    final_report: Optional[str]         # final Markdown report
