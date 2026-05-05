<p align="center">
  <h1 align="center">🤖 TradingAgents</h1>
  <p align="center">
    <strong>Multi-Agent LLM Financial Trading Framework</strong>
  </p>
  <p align="center">
    A production-ready Python implementation of the <a href="https://arxiv.org/abs/2412.20138">TradingAgents</a> research paper — where specialized LLM agents debate, analyze, and generate structured trading decisions with persistent memory.
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/LLM-GPT--4o--mini-green?logo=openai" />
  <img src="https://img.shields.io/badge/Groq-supported-orange?logo=data:image/svg+xml;base64," />
  <img src="https://img.shields.io/badge/streamlit-dashboard-FF4B4B?logo=streamlit" />
  <img src="https://img.shields.io/badge/docker-ready-2496ED?logo=docker" />
  <img src="https://img.shields.io/badge/license-MIT-lightgrey" />
</p>

---

## ✨ Features

- **Multi-Agent Pipeline** — Analyst Team → Bull/Bear Debate → Trader → Risk Manager → Fund Manager
- **Persistent Memory** — `SharedState` prevents information decay across the agent chain
- **Multi-Round Debate** — Configurable N-round bull vs. bear argumentation with facilitator synthesis
- **Structured Outputs** — Every agent emits typed JSON, not raw text
- **Switchable LLM Providers** — OpenAI (default) or Groq (free tier available)
- **Streamlit Dashboard** — Interactive equity curves, signal charts, debate history, and trade logs
- **CLI Runner** — Headless backtest execution from the terminal
- **Docker-Ready** — Single-command deployment via `docker-compose`

---

## 🏗️ Architecture

```
trading-agents/
├── .env.example         ← Copy to .env and add your API keys
├── requirements.txt     ← Python dependencies
├── config.py            ← Central configuration (API keys, model, etc.)
├── state.py             ← Shared persistent memory across all agents
├── agents.py            ← All LLM-powered agent classes + data tools
├── backtest.py          ← Backtesting engine with performance metrics
├── dashboard.py         ← Streamlit visual dashboard
├── run_backtest.py      ← CLI entry point
├── Dockerfile           ← Container image definition
├── docker-compose.yml   ← One-command local deployment
└── tests/               ← Unit & integration tests
    └── test_state.py
```

### Agent Pipeline

```
 Market Data (yfinance + Finnhub)
         │
    AnalystTeam
  ┌──────┼──────┐
Technical  Sentiment  Fundamentals
         │
  ResearcherDebate (Bull ⚔ Bear × N rounds → Facilitator)
         │
    TraderAgent  ──→  trade proposal (JSON)
         │
    RiskManager  ──→  position-size scaling factor
         │
    FundManager  ──→  final executable decision
         │
    Portfolio Execution
```

Each agent writes **structured dicts** to `SharedState` — never raw text — to prevent the "telephone effect" where information degrades across LLM calls.

---

## 🚀 Quickstart

### 1. Clone & install

```bash
git clone https://github.com/<your-username>/trading-agents.git
cd trading-agents
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env with your keys
```

| Key | Required | Source |
|-----|----------|--------|
| `OPENAI_API_KEY` | ✅ (if using OpenAI) | [platform.openai.com](https://platform.openai.com/api-keys) |
| `GROQ_API_KEY` | ✅ (if using Groq) | [console.groq.com](https://console.groq.com/keys) |
| `FINNHUB_API_KEY` | Optional | [finnhub.io](https://finnhub.io/register) (free tier) |

#### Using Groq (free LLM)

Set `LLM_PROVIDER=groq` and `GROQ_API_KEY=gsk_...` in your `.env` file. Recommended model: `llama-3.3-70b-versatile`.

### 3. Run the dashboard (recommended)

```bash
streamlit run dashboard.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### 4. Or run from the CLI

```bash
python run_backtest.py --symbol AAPL --start 2024-01-01 --end 2024-03-29
python run_backtest.py --symbol NVDA --start 2024-01-01 --end 2024-06-30 --capital 50000 --rounds 3
python run_backtest.py --symbol TSLA --quiet  # Suppress verbose agent output
```

---

## 🐳 Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f trading-agents

# Stop
docker-compose down
```

The dashboard will be available at [http://localhost:8501](http://localhost:8501).

---

## 📊 Performance Metrics

The backtester computes:

| Metric | Description |
|--------|-------------|
| Cumulative Return | Total % gain/loss over the period |
| Annualized Return | Extrapolated yearly return |
| Sharpe Ratio | Risk-adjusted return (annualized, 252 trading days) |
| Max Drawdown | Largest peak-to-trough loss |
| Final Portfolio Value | Ending dollar value |
| Number of Trades | Total buy/sell executions |

---

## 🧠 How It Works

### 1. Analyst Team
Three parallel data-gathering functions pull **technical indicators** (SMA-20, RSI-14 via yfinance), **news sentiment** (Finnhub headlines + VADER scoring), and **fundamental metrics** (P/E, market cap, 52-week range). An LLM synthesizes these into a concise analyst briefing.

### 2. Bull vs. Bear Debate
Two LLM "researchers" argue for N configurable rounds. The **Bull** sharpens a long thesis; the **Bear** counters with risks. A **Facilitator** agent synthesizes both perspectives into a final verdict with confidence level.

### 3. Trader → Risk → Fund Manager
- **TraderAgent**: Converts the debate verdict into a structured `{action, percentage}` JSON proposal.
- **RiskManager**: Reviews the proposal and returns a scaling factor (0.25–1.0).
- **FundManager**: Applies the risk factor and issues the final executable decision.

### 4. Portfolio Execution
The backtest engine executes the decision against historical prices, updating cash and share positions day by day.

---

## 💰 Cost Optimization Tips

| Strategy | Impact |
|----------|--------|
| Use `gpt-4o-mini` (default) | ~10× cheaper than `gpt-4o` |
| Use Groq free tier | $0 LLM cost |
| Set `DEBATE_ROUNDS=1` | Halves LLM calls per day |
| Shorter date ranges | Fewer trading days = fewer API calls |

A typical 3-month backtest with `gpt-4o-mini` and 2 debate rounds costs ~$0.50–$2.00 in API fees.

---

## 🧪 Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

## ⚠️ Disclaimer

This framework is for **research and educational purposes only**. It is not financial advice. Always consult a qualified financial advisor before making investment decisions. Past simulated performance does not guarantee future results.
