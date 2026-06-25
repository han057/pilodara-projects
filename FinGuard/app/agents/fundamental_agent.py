# app/agents/fundamental_agent.py
# Fundamental Analyst Agent — Oksana
#
# Responsibilities:
#   - Interpret FMP financial ratios for each ticker
#   - Classify risk signals per metric
#   - Produce structured analysis text for the Risk Officer

from typing import Any


def _interpret_zscore(z: float) -> str:
    if z > 3.0:
        return f"Altman Z-Score {z:.2f} → Safe zone (bankruptcy probability < 1%)"
    elif z > 1.8:
        return f"Altman Z-Score {z:.2f} → Grey zone (moderate distress risk)"
    return f"Altman Z-Score {z:.2f} → Distress zone (high bankruptcy risk)"


def _interpret_pe(pe: float) -> str:
    if pe <= 0:
        return "P/E ratio negative → company currently unprofitable"
    elif pe > 100:
        return f"P/E {pe:.1f}x → extreme growth premium, high valuation risk"
    elif pe > 40:
        return f"P/E {pe:.1f}x → elevated growth premium"
    elif pe > 15:
        return f"P/E {pe:.1f}x → within normal market range"
    return f"P/E {pe:.1f}x → below market average, potentially undervalued"


def _interpret_de(de: float) -> str:
    if de < 0.2:
        return f"Debt/Equity {de:.2f} → very conservative leverage"
    elif de < 0.5:
        return f"Debt/Equity {de:.2f} → low leverage, healthy balance sheet"
    elif de < 1.0:
        return f"Debt/Equity {de:.2f} → moderate leverage"
    elif de < 2.0:
        return f"Debt/Equity {de:.2f} → elevated leverage, monitor closely"
    return f"Debt/Equity {de:.2f} → high leverage, financial risk present"


def _interpret_growth(growth: float) -> str:
    pct = round(growth * 100, 1)
    if growth > 0.2:
        return f"Revenue growth {pct}% YoY → strong expansion"
    elif growth > 0.05:
        return f"Revenue growth {pct}% YoY → solid growth"
    elif growth > 0:
        return f"Revenue growth {pct}% YoY → modest growth"
    elif growth > -0.05:
        return f"Revenue growth {pct}% YoY → slight decline, watch trend"
    return f"Revenue growth {pct}% YoY → significant revenue contraction"


def _interpret_quick(quick: float) -> str:
    if quick > 2.0:
        return f"Quick ratio {quick:.2f} → excellent short-term liquidity"
    elif quick > 1.0:
        return f"Quick ratio {quick:.2f} → adequate liquidity"
    return f"Quick ratio {quick:.2f} → potential short-term liquidity pressure"


def analyze(fmp_data: dict) -> dict:
    """
    Interprets FMP financial data for a single ticker.

    Args:
        fmp_data: dict returned by fmp_agent.get_fmp_data()

    Returns:
        dict with keys:
            ticker          — stock ticker
            signals         — list of individual signal strings
            summary         — concatenated analysis string
            risk_level      — "LOW" | "MODERATE" | "HIGH"
    """
    ticker = fmp_data.get("ticker", "UNKNOWN")

    z      = fmp_data.get("altman_z_score") or 0.0
    pe     = fmp_data.get("pe_ratio")       or 0.0
    de     = fmp_data.get("debt_to_equity") or 0.0
    growth = fmp_data.get("revenue_growth") or 0.0
    quick  = fmp_data.get("quick_ratio")    or 0.0

    signals = [
        _interpret_zscore(z),
        _interpret_pe(pe),
        _interpret_de(de),
        _interpret_growth(growth),
        _interpret_quick(quick),
    ]

    # Overall risk level — driven primarily by Altman Z-Score
    if z > 3.0 and de < 0.5:
        risk_level = "LOW"
    elif z > 1.8 or de < 1.0:
        risk_level = "MODERATE"
    else:
        risk_level = "HIGH"

    return {
        "ticker":     ticker,
        "signals":    signals,
        "summary":    " | ".join(signals),
        "risk_level": risk_level,
    }
