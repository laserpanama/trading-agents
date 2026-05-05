"""
dashboard.py – Streamlit web UI for TradingAgents.

Run with:
    streamlit run dashboard.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf

from backtest import Backtest

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="TradingAgents Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    /* Dark card metric boxes */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem 1.25rem;
    }
    [data-testid="stMetricValue"] { color: #38bdf8; font-size: 1.8rem; }
    [data-testid="stMetricLabel"] { color: #94a3b8; }
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    /* Title gradient */
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown('<div class="hero-title">🤖 TradingAgents Dashboard</div>', unsafe_allow_html=True)
st.caption("Multi-Agent LLM Financial Trading Framework — Research & Backtesting")
st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Candlestick_chart_scheme_02-en.svg/200px-Candlestick_chart_scheme_02-en.svg.png",
        use_column_width=True,
    )
    st.header("⚙️ Backtest Configuration")

    symbol = st.text_input("📈 Stock Symbol", value="AAPL").upper()
    start_date = st.date_input("🗓️ Start Date", value=pd.to_datetime("2024-01-01"))
    end_date = st.date_input("🗓️ End Date", value=pd.to_datetime("2024-03-29"))
    capital = st.number_input("💵 Initial Capital ($)", value=100_000, step=10_000, min_value=1_000)
    debate_rounds = st.slider("🗣️ Debate Rounds (bull vs. bear)", min_value=1, max_value=5, value=2)
    verbose = st.toggle("🔍 Verbose agent output", value=False)

    st.divider()
    st.caption("⚠️ This tool is for research only — not financial advice.")

    run_btn = st.button("🚀 Run Backtest", type="primary", use_container_width=True)

# ── Main area ─────────────────────────────────────────────────────────────────

if not run_btn:
    # Landing / instructions
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("How it works")
        st.markdown(
            """
            1. **Analyst Team** gathers technical indicators, news sentiment, and fundamentals.
            2. **Bull vs. Bear Debate** — two LLM researchers argue N rounds, a facilitator synthesizes.
            3. **Trader Agent** proposes a trade (buy/sell/hold + size %).
            4. **Risk Manager** applies a position-size scaling factor.
            5. **Fund Manager** issues the final executable decision.
            6. The backtesting engine simulates the portfolio day by day.
            """
        )
    with col_r:
        st.subheader("Agent Pipeline")
        st.code(
            """
Market Data
    │
AnalystTeam (Technical + Sentiment + Fundamentals)
    │
ResearcherDebate (Bull ⚔ Bear × N rounds, Facilitator)
    │
TraderAgent  ──→  trade proposal (JSON)
    │
RiskManager  ──→  position scaling factor
    │
FundManager  ──→  final decision
    │
Portfolio Execution
            """,
            language="text",
        )
    st.info("Configure your backtest in the sidebar and click **Run Backtest** to start.")
    st.stop()

# ── Run backtest ──────────────────────────────────────────────────────────────

progress_bar = st.progress(0, text="Initializing agents…")

with st.spinner(f"Running TradingAgents for **{symbol}** ({start_date} → {end_date})…"):
    try:
        bt = Backtest(
            symbol=symbol,
            start_date=str(start_date),
            end_date=str(end_date),
            initial_capital=float(capital),
            debate_rounds=debate_rounds,
            verbose=verbose,
        )
        portfolio = bt.run()
        metrics = bt.metrics()
        trades = bt.trades_df()
        progress_bar.progress(100, text="Done ✅")
    except Exception as exc:
        st.error(f"❌ Backtest failed: {exc}")
        st.stop()

# ── Metrics row ───────────────────────────────────────────────────────────────

st.subheader("📊 Performance Summary")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Cumulative Return", f"{metrics['Cumulative Return (%)']:+.2f}%")
c2.metric("Annualized Return", f"{metrics['Annualized Return (%)']:+.2f}%")
c3.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")
c4.metric("Max Drawdown", f"{metrics['Max Drawdown (%)']:.2f}%")
c5.metric("Final Value", f"${metrics['Final Value ($)']:,.0f}")

st.divider()

# ── Equity curve ──────────────────────────────────────────────────────────────

st.subheader("📈 Equity Curve")

# Compare vs buy-and-hold
try:
    price_raw = yf.download(
        symbol, start=str(start_date), end=str(end_date), progress=False, auto_adjust=True
    )["Close"].squeeze()
    bh_value = price_raw / price_raw.iloc[0] * capital
    fig_eq = go.Figure()
    fig_eq.add_trace(
        go.Scatter(
            x=portfolio.index, y=portfolio, name="TradingAgents",
            line=dict(color="#38bdf8", width=2),
        )
    )
    fig_eq.add_trace(
        go.Scatter(
            x=bh_value.index, y=bh_value, name="Buy & Hold",
            line=dict(color="#f472b6", width=2, dash="dash"),
        )
    )
    fig_eq.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.8)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=0, r=0, t=30, b=0),
        height=400,
    )
    st.plotly_chart(fig_eq, use_container_width=True)
except Exception:
    fig_eq = px.line(x=portfolio.index, y=portfolio, labels={"x": "Date", "y": "Value ($)"})
    fig_eq.update_layout(template="plotly_dark")
    st.plotly_chart(fig_eq, use_container_width=True)

# ── Price chart with signals ──────────────────────────────────────────────────

st.subheader("🎯 Trading Signals on Price Chart")
try:
    price_series = yf.download(
        symbol, start=str(start_date), end=str(end_date), progress=False, auto_adjust=True
    )["Close"].squeeze()

    fig_sig = go.Figure()
    fig_sig.add_trace(
        go.Scatter(x=price_series.index, y=price_series, name="Close Price",
                   line=dict(color="#94a3b8", width=1.5))
    )

    if not trades.empty:
        buys = trades[trades["Action"] == "BUY"]
        sells = trades[trades["Action"] == "SELL"]
        if not buys.empty:
            fig_sig.add_trace(go.Scatter(
                x=pd.to_datetime(buys["Date"]), y=buys["Price"],
                mode="markers", name="BUY",
                marker=dict(color="#22c55e", size=12, symbol="triangle-up"),
            ))
        if not sells.empty:
            fig_sig.add_trace(go.Scatter(
                x=pd.to_datetime(sells["Date"]), y=sells["Price"],
                mode="markers", name="SELL",
                marker=dict(color="#ef4444", size=12, symbol="triangle-down"),
            ))

    fig_sig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.8)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=0, r=0, t=30, b=0),
        height=380,
    )
    st.plotly_chart(fig_sig, use_container_width=True)
except Exception as exc:
    st.warning(f"Could not render price chart: {exc}")

# ── Trade log ─────────────────────────────────────────────────────────────────

st.subheader("📋 Trade Log")
if trades.empty:
    st.info("No trades were executed during this period.")
else:
    # Color-code BUY / SELL
    def color_action(val: str) -> str:
        if val == "BUY":
            return "color: #22c55e; font-weight: bold"
        elif val == "SELL":
            return "color: #ef4444; font-weight: bold"
        return ""

    st.dataframe(
        trades.style.applymap(color_action, subset=["Action"]),
        use_container_width=True,
        hide_index=True,
    )
    csv_bytes = trades.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Trade Log (CSV)",
        data=csv_bytes,
        file_name=f"{symbol}_trades.csv",
        mime="text/csv",
    )

# ── Debate & agent log (collapsible) ─────────────────────────────────────────

if bt.state.debate_history.get(symbol):
    with st.expander("🗣️ Agent Debate History"):
        for entry in bt.state.debate_history[symbol]:
            st.markdown(f"**{entry['date']}**")
            cols = st.columns(2)
            with cols[0]:
                st.markdown("🟢 **Bull**")
                st.caption(entry["bull"][:400])
            with cols[1]:
                st.markdown("🔴 **Bear**")
                st.caption(entry["bear"][:400])
            st.info(f"**Facilitator verdict:** {entry['summary'][:300]}")
            st.divider()
