# interface_gui.py
# FinGuard — Professional GUI v2
# Palette: Petroleum Blue · Graphite · White · Semantic accents
# Run with: streamlit run interface_gui.py

import streamlit as st
from app.graph import graph

st.set_page_config(
    page_title="FinGuard · Risk Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",  # sidebar siempre abierto al arrancar
)

# ─────────────────────────────────────────────
# DESIGN SYSTEM
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

/* ── Reset ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Canvas ── */
.stApp { background: #F4F6F9; color: #1E1E1E; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: #0A3D62;
  border-right: none;
}
[data-testid="stSidebar"] * { color: #FFFFFF !important; }

.sb-logo {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: #FFFFFF !important;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.2rem 0 0.1rem 0;
}
.sb-logo .logo-badge {
  background: #2ECC71;
  color: #0A3D62 !important;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
  letter-spacing: 0.06em;
}
.sb-version {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.62rem;
  color: #5B8DB8 !important;
  letter-spacing: 0.05em;
  margin-bottom: 1.2rem;
}

.sb-section {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.6rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #5B8DB8 !important;
  padding: 0.9rem 0 0.4rem 0;
  border-top: 1px solid #154E7A;
  margin-top: 0.4rem;
}

/* ── Sidebar buttons (examples) ── */
[data-testid="stSidebar"] .stButton > button {
  background: transparent !important;
  color: #C8DFF0 !important;
  border: 1px solid #154E7A !important;
  border-radius: 4px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.75rem !important;
  font-weight: 400 !important;
  text-align: left !important;
  padding: 0.35rem 0.7rem !important;
  letter-spacing: 0 !important;
  margin-bottom: 0.15rem !important;
  transition: all 0.12s !important;
  width: 100% !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: #154E7A !important;
  border-color: #2ECC71 !important;
  color: #FFFFFF !important;
}

/* ── Ticker rows in sidebar ── */
.sb-ticker {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.28rem 0;
  border-bottom: 1px solid #154E7A;
  font-size: 0.75rem;
}
.sb-ticker:last-child { border-bottom: none; }
.sb-sym {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.68rem;
  font-weight: 600;
  color: #0A3D62 !important;
  background: #2ECC71;
  padding: 0.08rem 0.35rem;
  border-radius: 2px;
  min-width: 44px;
  text-align: center;
}
.sb-name { color: #A8C8E0 !important; font-size: 0.73rem; }
.sb-dot { width:5px; height:5px; background:#2ECC71; border-radius:50%; margin-left:auto; flex-shrink:0; }

.sb-autonote {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.6rem;
  color: #5B8DB8 !important;
  margin-top: 0.5rem;
  line-height: 1.5;
}

/* ── Historial ── */
.sb-hist-item {
  background: #154E7A;
  border-radius: 4px;
  padding: 0.35rem 0.6rem;
  margin-bottom: 0.25rem;
  font-size: 0.72rem;
  color: #C8DFF0 !important;
  cursor: pointer;
  border: 1px solid transparent;
  transition: border-color 0.12s;
}
.sb-hist-item:hover { border-color: #2ECC71; }
.sb-hist-ticker {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.62rem;
  color: #2ECC71 !important;
  margin-bottom: 0.1rem;
}

/* ── Main hero ── */
.main-hero {
  background: #0A3D62;
  border-radius: 8px;
  padding: 2rem 2.4rem 1.8rem;
  margin-bottom: 1.5rem;
  position: relative;
  overflow: hidden;
}
.main-hero::before {
  content: '';
  position: absolute;
  right: -40px; top: -40px;
  width: 200px; height: 200px;
  background: radial-gradient(circle, #154E7A 0%, transparent 70%);
  pointer-events: none;
}
.hero-eyebrow {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #5B8DB8;
  margin-bottom: 0.5rem;
}
.hero-title {
  font-family: 'Inter', sans-serif;
  font-size: 1.9rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #FFFFFF;
  line-height: 1.15;
  margin-bottom: 0.35rem;
}
.hero-title .accent { color: #2ECC71; }
.hero-sub {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.68rem;
  color: #5B8DB8;
  letter-spacing: 0.04em;
  margin-bottom: 1.4rem;
}

/* ── Input inside hero ── */
.stTextInput > div > div > input {
  background: #FFFFFF !important;
  border: 1.5px solid #E0E6ED !important;
  border-radius: 5px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.92rem !important;
  color: #1E1E1E !important;
  padding: 0.6rem 0.9rem !important;
}
.stTextInput > div > div > input:focus {
  border-color: #0A3D62 !important;
  box-shadow: 0 0 0 3px #0A3D6218 !important;
}

/* ── Analyze button ── */
[data-testid="stBaseButton-primary"] {
  background: #2ECC71 !important;
  color: #0A3D62 !important;
  border: none !important;
  border-radius: 5px !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 700 !important;
  font-size: 0.82rem !important;
  letter-spacing: 0.04em !important;
  padding: 0.58rem 1.4rem !important;
  transition: opacity 0.12s !important;
}
[data-testid="stBaseButton-primary"]:hover { opacity: 0.88 !important; }

/* ── Risk summary card ── */
.risk-card {
  background: #FFFFFF;
  border-radius: 7px;
  border: 1px solid #E0E6ED;
  border-top: 4px solid var(--risk-color);
  padding: 1.2rem 1.4rem;
  margin-bottom: 1rem;
}
.risk-card-eyebrow {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.62rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #6B7280;
  margin-bottom: 0.5rem;
}
.risk-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: var(--risk-bg);
  color: var(--risk-color);
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.25rem 0.7rem;
  border-radius: 20px;
  border: 1px solid var(--risk-color);
  margin-bottom: 0.8rem;
}
.zscore-big {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 2.6rem;
  font-weight: 600;
  color: var(--risk-color);
  line-height: 1;
  margin-bottom: 0.2rem;
}
.zscore-label {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.62rem;
  color: #6B7280;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 0.8rem;
}
.risk-signals li {
  font-size: 0.8rem;
  color: #2B2B2B;
  margin-bottom: 0.2rem;
  line-height: 1.5;
}

/* ── Metrics table ── */
.metrics-section {
  background: #FFFFFF;
  border-radius: 7px;
  border: 1px solid #E0E6ED;
  overflow: hidden;
  margin-bottom: 1rem;
}
.metrics-section-header {
  background: #F4F6F9;
  padding: 0.6rem 1.1rem;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #6B7280;
  border-bottom: 1px solid #E0E6ED;
  cursor: pointer;
}
.metrics-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}
.metrics-table th {
  background: #F4F6F9;
  padding: 0.45rem 1rem;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.63rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #6B7280;
  border-bottom: 1px solid #E0E6ED;
  text-align: left;
  font-weight: 500;
}
.metrics-table td {
  padding: 0.5rem 1rem;
  border-bottom: 1px solid #F4F6F9;
  color: #1E1E1E;
  vertical-align: middle;
}
.metrics-table tr:last-child td { border-bottom: none; }
.metrics-table tr:hover td { background: #F9FAFB; }
.metric-name { font-weight: 500; color: #374151; }
.metric-val {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.82rem;
  font-weight: 600;
}
.val-green { color: #2ECC71; }
.val-orange { color: #F39C12; }
.val-red { color: #E74C3C; }
.val-neutral { color: #0A3D62; }
.metric-cat {
  background: #F4F6F9;
  padding: 0.35rem 1rem;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.63rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #9CA3AF;
  border-bottom: 1px solid #E0E6ED;
}

/* ── SEC RAG card ── */
.rag-card {
  background: #FFFFFF;
  border: 1px solid #E0E6ED;
  border-left: 3px solid #0A3D62;
  border-radius: 0 6px 6px 0;
  padding: 0.85rem 1.1rem;
  margin-bottom: 0.6rem;
}
.rag-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.4rem;
}
.rag-ticker {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.68rem;
  font-weight: 600;
  background: #EBF5FF;
  color: #0A3D62;
  padding: 0.1rem 0.4rem;
  border-radius: 3px;
}
.rag-source {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.63rem;
  color: #9CA3AF;
}
.rag-text {
  font-size: 0.79rem;
  color: #374151;
  line-height: 1.6;
}

/* ── Agent flow card ── */
.agent-flow {
  background: #FFFFFF;
  border-radius: 7px;
  border: 1px solid #E0E6ED;
  padding: 1rem 1.2rem;
}
.agent-step {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.6rem 0;
  border-bottom: 1px solid #F4F6F9;
}
.agent-step:last-child { border-bottom: none; }
.agent-icon {
  width: 28px; height: 28px;
  background: #EBF5FF;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  flex-shrink: 0;
}
.agent-icon.done { background: #D1FAE5; }
.agent-name {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.72rem;
  font-weight: 600;
  color: #0A3D62;
  margin-bottom: 0.15rem;
}
.agent-desc { font-size: 0.75rem; color: #6B7280; line-height: 1.4; }

/* ── Report container ── */
.report-wrap {
  background: #FFFFFF;
  border-radius: 7px;
  border: 1px solid #E0E6ED;
  padding: 1.6rem 1.8rem;
  margin-top: 1rem;
  font-size: 0.88rem;
  line-height: 1.75;
  color: #1E1E1E;
}

/* ── Section title ── */
.section-title {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #6B7280;
  margin: 1.2rem 0 0.6rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.section-title::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #E0E6ED;
}

/* ── Misc ── */
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { visibility: hidden; height: 0; }

/* ── Sidebar siempre visible y fijo ── */
[data-testid="stSidebar"] {
  transform: translateX(0) !important;
  min-width: 240px !important;
  max-width: 280px !important;
  visibility: visible !important;
  display: block !important;
}

/* Ocultar solo el botón de colapsar dentro del sidebar */
[data-testid="stSidebar"] [data-testid="stSidebarNavCollapseButton"] {
  display: none !important;
}

/* Ocultar el botón flotante de expandir (cuando estaría colapsado) */
[data-testid="collapsedControl"] {
  visibility: hidden !important;
  pointer-events: none !important;
}
.block-container { padding-top: 1.2rem !important; max-width: 1200px !important; }
hr { border-color: #E0E6ED !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def risk_colors(level: str):
    """Returns (css_color, css_bg, emoji, label) for a risk level."""
    level = (level or "MODERATE").upper()
    return {
        "LOW":      ("#2ECC71", "#D1FAE5", "✅", "SAFE"),
        "MODERATE": ("#F39C12", "#FEF3C7", "⚠️", "MONITOR"),
        "HIGH":     ("#E74C3C", "#FEE2E2", "🔴", "HIGH RISK"),
    }.get(level, ("#F39C12", "#FEF3C7", "⚠️", "MONITOR"))

def fmt_val(v, pct=False, decimals=2, prefix=""):
    if v is None: return "—"
    if pct: return f"{v*100:.1f}%"
    return f"{prefix}{v:.{decimals}f}"

def val_class(col, v):
    if v is None: return "val-neutral"
    if col in ("roe", "roa", "revenue_growth", "gross_margin"):
        return "val-green" if v > 0 else "val-red"
    if col == "altman_z_score":
        if v > 3.0: return "val-green"
        if v > 1.8: return "val-orange"
        return "val-red"
    if col == "quick_ratio":
        if v > 1.0: return "val-green"
        return "val-orange"
    if col == "debt_to_equity":
        if v < 0.5: return "val-green"
        if v < 1.5: return "val-orange"
        return "val-red"
    return "val-neutral"

METRIC_CATEGORIES = {
    "Liquidity":      [("Quick Ratio", "quick_ratio", False), ("Current Ratio", "current_ratio", False)],
    "Profitability":  [("ROE", "roe", True), ("ROA", "roa", True), ("Gross Margin", "gross_margin", True)],
    "Solvency":       [("Debt / Equity", "debt_to_equity", False), ("Altman Z-Score", "altman_z_score", False)],
    "Growth":         [("Revenue Growth YoY", "revenue_growth", True)],
    "Valuation":      [("P/E Ratio", "pe_ratio", False), ("Stock Price", "current_price", False)],
}

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "query" not in st.session_state:     st.session_state["query"] = ""
if "history" not in st.session_state:   st.session_state["history"] = []
if "last_result" not in st.session_state: st.session_state["last_result"] = None

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-logo"><span class="logo-badge">FG</span> FinGuard</div>
    <div class="sb-version">v2.0 · Risk Intelligence Platform</div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-section">Quick queries</div>', unsafe_allow_html=True)
    examples = [
        "Analyze Tesla bankruptcy risk",
        "Compare Tesla and Apple risk",
        "Is Nvidia a safe investment?",
        "Tell me about the iPhone company",
        "Compare Microsoft and Amazon risk",
        "Meta's financial health",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            st.session_state["query"] = ex
            st.rerun()

    st.markdown('<div class="sb-section">Indexed companies</div>', unsafe_allow_html=True)
    companies = {
        "TSLA": "Tesla", "AAPL": "Apple", "NVDA": "Nvidia",
        "MSFT": "Microsoft", "AMZN": "Amazon", "META": "Meta",
        "GOOGL": "Google", "EPAM": "EPAM Systems",
    }
    rows = ""
    for sym, name in companies.items():
        rows += f'<div class="sb-ticker"><span class="sb-sym">{sym}</span><span class="sb-name">{name}</span><span class="sb-dot"></span></div>'
    st.markdown(rows, unsafe_allow_html=True)
    st.markdown('<div class="sb-autonote">Any S&P 500 ticker auto-indexes on first query.</div>', unsafe_allow_html=True)

    if st.session_state["history"]:
        st.markdown('<div class="sb-section">Recent analyses</div>', unsafe_allow_html=True)
        for h in reversed(st.session_state["history"][-5:]):
            tstr = " · ".join(h.get("tickers", []))
            q    = h.get("query", "")[:38]
            st.markdown(f'<div class="sb-hist-item"><div class="sb-hist-ticker">{tstr}</div>{q}{"…" if len(h.get("query",""))>38 else ""}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-hero">
  <div class="hero-eyebrow">Multi-agent financial risk analysis</div>
  <div class="hero-title">Financial <span class="accent">Risk</span> Intelligence</div>
  <div class="hero-sub">SEC EDGAR · FMP API · ChromaDB · LangGraph · qwen3:8b</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# INPUT
# ─────────────────────────────────────────────
col_q, col_btn = st.columns([5, 1], gap="small")
with col_q:
    query = st.text_input(
        label="q", label_visibility="collapsed",
        value=st.session_state.get("query", ""),
        placeholder="e.g.  Compare Tesla and Apple risk  ·  Is Nvidia a safe investment?",
    )
with col_btn:
    run = st.button("Analyze →", type="primary", use_container_width=True)

# ─────────────────────────────────────────────
# PIPELINE
# ─────────────────────────────────────────────
if run:
    if not query.strip():
        st.warning("Please enter a query.")
    else:
        with st.spinner("Running multi-agent pipeline…"):
            try:
                result = graph.invoke({"query": query})
                result["query"] = query
                st.session_state["last_result"] = result
                if not any(h.get("query") == query for h in st.session_state["history"]):
                    st.session_state["history"].append({
                        "query":   query,
                        "tickers": result.get("tickers", []),
                    })
                st.rerun()
            except Exception as e:
                st.error(f"Pipeline error: {e}")
                st.info("Make sure Ollama is running: `ollama serve`")

# ─────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────
result = st.session_state.get("last_result")

if result:
    tickers   = result.get("tickers", [])
    reasoning = result.get("supervisor_reasoning", "")
    report    = result.get("final_report", "")
    rag_list  = result.get("rag_results", [])
    fmp_list  = result.get("fmp_results", [])
    analyses  = result.get("analyses", [])

    fmp_by      = {f["ticker"]: f for f in fmp_list}
    analysis_by = {a["ticker"]: a for a in analyses}

    # ── Layout: main col + right panel ──
    col_main, col_panel = st.columns([3, 1], gap="large")

    with col_main:
        # ── Risk summary cards ──
        st.markdown('<div class="section-title">Risk Assessment</div>', unsafe_allow_html=True)

        for ticker in tickers:
            fmp  = fmp_by.get(ticker, {})
            ana  = analysis_by.get(ticker, {})
            level = ana.get("risk_level", "MODERATE")
            color, bg, emoji, label = risk_colors(level)
            z     = fmp.get("altman_z_score")
            zscore_str = f"{z:.2f}" if z is not None else "N/A"
            signals = ana.get("signals", [])

            st.markdown(f"""
            <div class="risk-card" style="--risk-color:{color}; --risk-bg:{bg}">
              <div class="risk-card-eyebrow">{ticker}</div>
              <div class="risk-badge">{emoji} {label}</div>
              <div class="zscore-big">{zscore_str}</div>
              <div class="zscore-label">Altman Z-Score</div>
              <ul class="risk-signals">
                {"".join(f"<li>{s}</li>" for s in signals[:3])}
              </ul>
            </div>
            """, unsafe_allow_html=True)

        # ── Metrics by category ──
        if fmp_list:
            st.markdown('<div class="section-title">Financial Metrics</div>', unsafe_allow_html=True)

            for ticker in tickers:
                fmp = fmp_by.get(ticker, {})
                if not fmp: continue

                with st.expander(f"{ticker} — detailed metrics", expanded=len(tickers) == 1):
                    html = '<div class="metrics-section"><table class="metrics-table"><thead><tr><th>Category</th><th>Metric</th><th>Value</th></tr></thead><tbody>'
                    for cat, metrics in METRIC_CATEGORIES.items():
                        # Fila de categoría
                        html += f'<tr><td colspan="3" class="metric-cat">{cat}</td></tr>'
                        for label, key, is_pct in metrics:
                            raw = fmp.get(key)
                            val = fmt_val(raw, pct=is_pct)
                            cls = val_class(key, raw)
                            html += f'<tr><td></td><td class="metric-name">{label}</td><td class="metric-val {cls}">{val}</td></tr>'
                    html += "</tbody></table></div>"
                    st.markdown(html, unsafe_allow_html=True)

        # ── Full report ──
        if report:
            st.markdown('<div class="section-title">Full Report</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="report-wrap">', unsafe_allow_html=True)
            st.markdown(report)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── SEC RAG sources ──
        if rag_list:
            st.markdown('<div class="section-title">SEC Filing Context</div>', unsafe_allow_html=True)
            for rag in rag_list:
                ticker  = rag.get("ticker", "—")
                source  = rag.get("fuente", "N/A")
                preview = (rag.get("texto") or "")[:320]
                st.markdown(f"""
                <div class="rag-card">
                  <div class="rag-header">
                    <span class="rag-ticker">{ticker}</span>
                    <span class="rag-source">{source}</span>
                  </div>
                  <div class="rag-text">{preview}…</div>
                </div>
                """, unsafe_allow_html=True)

    with col_panel:
        # ── Agent flow ──
        st.markdown('<div class="section-title">Agent Pipeline</div>', unsafe_allow_html=True)
        agents = [
            ("🧠", "Supervisor", "Tickers extracted · Query reasoned"),
            ("📄", "RAG Agent",  "SEC 10-K retrieved from ChromaDB"),
            ("📈", "FMP Agent",  "Real-time market data fetched"),
            ("🔬", "Analyst",    "Ratios interpreted · Signals emitted"),
            ("🛡️", "Risk Officer","Final report generated"),
        ]
        flow_html = '<div class="agent-flow">'
        for icon, name, desc in agents:
            flow_html += f"""
            <div class="agent-step">
              <div class="agent-icon done">{icon}</div>
              <div>
                <div class="agent-name">{name}</div>
                <div class="agent-desc">{desc}</div>
              </div>
            </div>"""
        flow_html += '</div>'
        st.markdown(flow_html, unsafe_allow_html=True)

        # ── Supervisor reasoning ──
        st.markdown('<div class="section-title" style="margin-top:1rem">Supervisor</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="agent-flow">
          <div style="font-family:'IBM Plex Mono',monospace;font-size:0.62rem;color:#6B7280;
                      letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.4rem">
            Tickers
          </div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:0.8rem;color:#0A3D62;
                      font-weight:600;margin-bottom:0.8rem">
            {" · ".join(tickers)}
          </div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:0.62rem;color:#6B7280;
                      letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.4rem">
            Reasoning
          </div>
          <div style="font-size:0.75rem;color:#374151;line-height:1.55">{reasoning}</div>
        </div>
        """, unsafe_allow_html=True)

else:
    # ── Empty state ──
    st.markdown("""
    <div style="text-align:center;padding:3.5rem 0;color:#9CA3AF;
                font-family:'IBM Plex Mono',monospace;font-size:0.78rem;letter-spacing:0.04em">
      Enter a query above to start the multi-agent pipeline.
    </div>
    """, unsafe_allow_html=True)