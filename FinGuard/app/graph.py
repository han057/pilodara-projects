# app/graph.py
# LangGraph orchestration — José
#
# This file contains ONLY graph topology:
#   - node registration
#   - edge definitions
#   - routing logic
#
# All business logic lives in app/agents/*.py
# This is the "map of the metro" — not what happens inside each station.

import json
import time
from pathlib import Path

from langgraph.graph import StateGraph, END

from app.state import FinancialState
from app.agents.supervisor_agent  import run_supervisor
from app.agents.rag_agent         import retrieve        as rag_retrieve
from app.agents.fmp_agent         import get_fmp_data
from app.agents.fundamental_agent import analyze         as fundamental_analyze
from app.agents.risk_officer      import generate_report


# ---------------------------------------------------------------------------
# AGENT NODES
# Each node does ONE thing: call its agent and return state updates.
# No business logic here.
# ---------------------------------------------------------------------------

def supervisor_node(state: FinancialState) -> dict:
    print("\n--- [Supervisor LLM] Reasoning about query ---")
    decision = run_supervisor(state["query"])

    print(f"   Tickers identified : {decision['tickers']}")
    print(f"   Reasoning          : {decision['reasoning']}")

    return {
        "tickers":              decision["tickers"],
        "supervisor_reasoning": decision["reasoning"],
        "current_agent":        "data_collectors",
        "rag_results":          [],
        "fmp_results":          [],
        "analyses":             [],
    }


def rag_node(state: FinancialState) -> dict:
    print("--- [RAG Agent (Natalia)] Querying ChromaDB ---")
    query   = state["query"]
    results = []

    for ticker in state["tickers"]:
        result = rag_retrieve(ticker, query)
        results.append(result)

        # Audit trail
        Path("traces.jsonl").open("a").write(
            json.dumps({
                "agent":      "rag",
                "ticker":     ticker,
                "query":      query,
                "source":     result["fuente"],
                "found":      result["found"],
                "timestamp":  time.strftime("%Y-%m-%dT%H:%M:%S"),
            }, ensure_ascii=False) + "\n"
        )

    return {"rag_results": results}


def fmp_node(state: FinancialState) -> dict:
    print("--- [FMP Agent (Oksana)] Calling FMP API ---")
    results = [get_fmp_data(ticker) for ticker in state["tickers"]]
    return {"fmp_results": results}


def fundamental_node(state: FinancialState) -> dict:
    print("--- [Fundamental Analyst (Oksana)] Interpreting ratios ---")
    analyses = [fundamental_analyze(fmp) for fmp in state["fmp_results"]]
    return {"analyses": analyses}


def risk_officer_node(state: FinancialState) -> dict:
    print("--- [Risk Officer (José)] Generating final report ---")
    report = generate_report(
        tickers   = state["tickers"],
        reasoning = state["supervisor_reasoning"],
        rag_list  = state["rag_results"],
        fmp_list  = state["fmp_results"],
        analyses  = state["analyses"],
    )
    return {"final_report": report}


# ---------------------------------------------------------------------------
# GRAPH CONSTRUCTION
# ---------------------------------------------------------------------------

builder = StateGraph(FinancialState)

builder.add_node("supervisor",          supervisor_node)
builder.add_node("rag_agent",           rag_node)
builder.add_node("fmp_agent",           fmp_node)
builder.add_node("fundamental_agent",   fundamental_node)
builder.add_node("risk_officer",        risk_officer_node)

builder.set_entry_point("supervisor")

# Parallel execution: supervisor triggers RAG and FMP simultaneously
builder.add_edge("supervisor",        "rag_agent")
builder.add_edge("supervisor",        "fmp_agent")

# Synchronization: both feed into fundamental analyst
builder.add_edge("rag_agent",         "fundamental_agent")
builder.add_edge("fmp_agent",         "fundamental_agent")

# Final chain
builder.add_edge("fundamental_agent", "risk_officer")
builder.add_edge("risk_officer",      END)

graph = builder.compile()
