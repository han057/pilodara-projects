# app/agents/supervisor_agent.py
# ReAct Supervisor Agent — José
#
# Responsibilities:
#   - Receive the user's natural language query
#   - Use qwen3:8b LLM to reason about intent
#   - Extract company tickers (handles aliases: "iPhone company" → AAPL)
#   - Decide which data sources are needed (RAG, FMP, or both)
#   - Detect comparison mode (multiple companies)
#
# This is the ReAct pattern: Reasoning + Acting
# The LLM thinks before deciding what to do — not a hardcoded if/else router.

import json
import os
from langchain_ollama import ChatOllama


_LLM = ChatOllama(
    model="qwen3:8b",
    temperature=0,
    base_url=os.getenv("OLLAMA_HOST", "http://ollama:11434"),
)

_PROMPT_TEMPLATE = """You are a financial analysis supervisor for a multi-agent system.

A user has submitted the following query:
"{query}"

Your task is to analyze this query and decide how to route it through the system.

Think step by step:
1. Identify ALL companies or brands mentioned (including indirect references)
2. Map each company to its official stock ticker symbol
3. Decide if SEC filing search (RAG) is needed for historical context
4. Decide if real-time FMP API data is needed for current ratios
5. Detect if the user wants a comparison between multiple companies

Known ticker mappings (not exhaustive — use your knowledge for others):
- Tesla, electric cars, Elon Musk's car company → TSLA
- Apple, iPhone, iPad, Mac, iOS company → AAPL
- Nvidia, GPU, AI chips, graphics cards → NVDA
- Microsoft, Windows, Azure, Office → MSFT
- Amazon, AWS, e-commerce giant → AMZN
- Google, Alphabet, YouTube, search engine → GOOGL
- Meta, Facebook, Instagram, WhatsApp → META

Rules:
- Always return valid JSON — no markdown, no explanation outside the JSON
- "tickers" must be a list even if only one company
- "needs_rag" is true when the user asks about filings, history, or risk factors
- "needs_fmp" is true when the user asks about price, ratios, or current metrics
- "comparison_mode" is true when two or more companies are mentioned
- "reasoning" should explain your decision in one or two sentences

Reply ONLY with this JSON structure:
{{
  "tickers": ["TSLA"],
  "needs_rag": true,
  "needs_fmp": true,
  "comparison_mode": false,
  "reasoning": "User asked about Tesla bankruptcy risk. SEC filings provide historical context; FMP provides real-time solvency ratios."
}}"""


def run_supervisor(query: str) -> dict:
    """
    Sends the user query to qwen3:8b and parses the routing decision.

    Args:
        query: natural language financial question from the user

    Returns:
        dict with keys:
            tickers         — list of ticker symbols (e.g. ["TSLA", "AAPL"])
            needs_rag       — bool: whether to run ChromaDB search
            needs_fmp       — bool: whether to call FMP API
            comparison_mode — bool: whether multiple companies are involved
            reasoning       — LLM chain-of-thought explanation
    """
    prompt   = _PROMPT_TEMPLATE.format(query=query)
    response = _LLM.invoke(prompt)
    raw      = response.content.strip()

    # Strip markdown code fences if the LLM adds them
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    # Strip <think>...</think> tags if model includes reasoning trace
    if "<think>" in raw:
        raw = raw.split("</think>")[-1].strip()

    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        # Safe fallback — never crash the pipeline
        print(f"   [Supervisor] Could not parse LLM response. Using fallback.")
        return {
            "tickers":         ["TSLA"],
            "needs_rag":       True,
            "needs_fmp":       True,
            "comparison_mode": False,
            "reasoning":       "Fallback: LLM response could not be parsed as JSON.",
        }

