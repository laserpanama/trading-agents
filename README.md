# TradingAgents – Multi-Agent LLM Financial Trading Framework

A Python implementation of the **TradingAgents** paper: a multi-agent LLM system where specialized analyst agents debate, refine, and ultimately produce structured trading decisions — all with persistent memory and a live Streamlit dashboard.

---

## Architecture

```
trading-agents/
├── .env.example        ← Copy to .env and add your API keys
├── requirements.txt
├── config.py           ← Central configuration (API keys, model, etc.)
├── state.py            ← Shared persistent memory across all agents
├── agents.py           ← All LLM-powered agent classes + data tools
├── backtest.py         ← Backtesting engine with metrics
├── dashboard.py        ← Streamlit visual dashboard
└── run_backtest.py     ← CLI entry point
```

### Agent Pipeline

```
Market Data (yfinance, Finnhub)
        │
   AnalystTeam
 ┌─────┴──────┐
Technical   Sentiment  Fundamentals
        │
 ResearcherDebate (Bull ⚔ Bear, N rounds, Facilitator)
        │
   TraderAgent  ──→  trade proposal
        │
   RiskManager  ──→  position sizing adjustment
        │
   FundManager  ──→  final JSON decision
        │
   Portfolio Execution
```

---

## Quickstart

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and FINNHUB_API_KEY
```

- **OpenAI API key**: https://platform.openai.com/api-keys
- **Finnhub API key** (free tier works): https://finnhub.io/register

### 3. Run the dashboard (recommended)

```bash
streamlit run dashboard.py
```

Open http://localhost:8501 in your browser.

### 4. Or run a backtest from the CLI

```bash
python run_backtest.py --symbol AAPL --start 2024-01-01 --end 2024-03-29
```

---

## Performance Metrics

The backtester computes:

| Metric | Description |
|--------|-------------|
| Cumulative Return | Total % gain/loss over the period |
| Sharpe Ratio | Risk-adjusted return (annualized) |
| Max Drawdown | Largest peak-to-trough loss |
| Final Portfolio Value | Ending dollar value |

---

## Cost Optimization Tips

- Use `gpt-4o-mini` (default) to keep API costs low
- Reduce `DEBATE_ROUNDS` to 1 for faster/cheaper runs
- Cache results: analyst reports are stored in `SharedState` to avoid redundant calls
- For long backtests, run only on key dates (e.g., weekly rebalancing)

---

## Disclaimer

This framework is for **research and educational purposes only**. It is not financial advice. Always consult a qualified financial advisor before making investment decisions. Past simulated performance does not guarantee future results.
