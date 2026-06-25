# app/agents/fmp_agent.py
# FMP Analyst Agent
# Fetches real-time financial data using FMP stable endpoints (post Aug 2025)

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)
FMP_KEY = os.getenv("FMP_API_KEY")

BASE_URL = "https://financialmodelingprep.com/stable"


def _get(endpoint: str, params: dict = {}) -> list | None:
    """Generic GET request to FMP stable API with error handling."""
    params["apikey"] = FMP_KEY
    try:
        response = requests.get(
            f"{BASE_URL}/{endpoint}",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print(f"   [FMP] Timeout on {endpoint}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"   [FMP] Request failed on {endpoint}: {e}")
        return None


def _calculate_altman_z(
    balance: dict,
    income: dict,
    metrics: dict
) -> float | None:
    """
    Calculates Altman Z-Score using real balance sheet data.
    Formula: Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5

    X1 = Working Capital / Total Assets
    X2 = Retained Earnings / Total Assets
    X3 = EBIT (Operating Income) / Total Assets
    X4 = Market Cap / Total Liabilities
    X5 = Revenue / Total Assets

    Zones:
      Z > 3.0  → Safe zone
      1.8-3.0  → Grey zone
      Z < 1.8  → Distress zone
    """
    try:
        # From balance sheet
        total_assets      = balance.get("totalAssets", 0)
        retained_earnings = balance.get("retainedEarnings", 0)
        total_liabilities = balance.get("totalLiabilities", 1)

        # From key metrics
        working_capital   = metrics.get("workingCapital", 0)
        market_cap        = metrics.get("marketCap", 0)

        # From income statement
        revenue           = income.get("revenue", 0)
        ebit              = income.get("operatingIncome", 0)

        if not total_assets or total_assets == 0:
            return None

        x1 = working_capital / total_assets
        x2 = retained_earnings / total_assets
        x3 = ebit / total_assets
        x4 = market_cap / max(total_liabilities, 1)
        x5 = revenue / total_assets

        z = 1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + 1.0*x5
        return round(z, 2)

    except Exception as e:
        print(f"   [FMP] Z-Score calculation error: {e}")
        return None


def get_fmp_data(ticker: str) -> dict:
    """
    Fetches key financial metrics for a given ticker.
    Uses FMP stable endpoints available on free plan.
    Makes 4 API calls: quote, ratios, key-metrics,
    income-statement, balance-sheet-statement.
    """
    print(f"   [FMP] Fetching real-time data for {ticker}...")

    result = {
        "ticker":         ticker,
        "current_price":  None,
        "pe_ratio":       None,
        "debt_to_equity": None,
        "roe":            None,
        "roa":            None,
        "gross_margin":   None,
        "quick_ratio":    None,
        "altman_z_score": None,
        "revenue_growth": None,
        "news_summary":   "News not available on current plan.",
        "source":         "FMP API (stable)",
    }

    # --- Call 1: Real-time stock price ---
    quote = _get("quote", params={"symbol": ticker})
    if quote and len(quote) > 0:
        result["current_price"] = quote[0].get("price")
        print(f"   [FMP] ✓ Price: ${result['current_price']}")

    # --- Call 2: Financial ratios ---
    ratios = _get("ratios", params={"symbol": ticker, "limit": 1})
    if ratios and len(ratios) > 0:
        r = ratios[0]
        result["pe_ratio"]       = round(r.get("priceToEarningsRatio", 0), 2)
        result["debt_to_equity"] = round(r.get("debtToEquityRatio", 0), 2)
        result["gross_margin"]   = round(r.get("grossProfitMargin", 0), 4)
        result["quick_ratio"]    = round(r.get("quickRatio", 0), 2)
        print(f"   [FMP] ✓ P/E: {result['pe_ratio']} | D/E: {result['debt_to_equity']} | Quick: {result['quick_ratio']}")

    # --- Call 3: Key metrics (ROE, ROA, working capital, market cap) ---
    metrics = _get("key-metrics", params={"symbol": ticker, "limit": 1})
    if metrics and len(metrics) > 0:
        m = metrics[0]
        result["roe"] = round(m.get("returnOnEquity", 0), 4)
        result["roa"] = round(m.get("returnOnAssets", 0), 4)
        print(f"   [FMP] ✓ ROE: {result['roe']} | ROA: {result['roa']}")

    # --- Call 4: Income statement (revenue growth + EBIT for Z-Score) ---
    income = _get("income-statement", params={"symbol": ticker, "limit": 2})
    if income and len(income) >= 2:
        rev_now  = income[0].get("revenue", 0)
        rev_prev = income[1].get("revenue", 1)
        if rev_prev > 0:
            growth = (rev_now - rev_prev) / rev_prev
            result["revenue_growth"] = round(growth, 4)
            print(f"   [FMP] ✓ Revenue growth YoY: {result['revenue_growth']*100:.1f}%")

    # --- Call 5: Balance sheet (totalAssets, retainedEarnings, totalDebt) ---
    balance = _get("balance-sheet-statement", params={"symbol": ticker, "limit": 1})
    if balance and len(balance) > 0:
        total_assets = balance[0].get("totalAssets", 0)
        total_debt   = balance[0].get("totalDebt", 0)
        retained     = balance[0].get("retainedEarnings", 0)
        print(f"   [FMP] ✓ Total assets: ${total_assets:,} | Debt: ${total_debt:,} | Retained: ${retained:,}")

    # --- Altman Z-Score calculation ---
    if balance and income and metrics:
        z = _calculate_altman_z(balance[0], income[0], metrics[0])
        result["altman_z_score"] = z
        if z is not None:
            if z > 3.0:
                zone = "Safe zone ✅"
            elif z > 1.8:
                zone = "Grey zone ⚠️"
            else:
                zone = "Distress zone ❌"
            print(f"   [FMP] ✓ Altman Z-Score: {z} — {zone}")

    print(f"   [FMP] Data collection complete for {ticker}.")
    return result
