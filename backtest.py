"""
backtest.py – Portfolio simulation engine.

For each trading day in the date range the full agent pipeline fires:
  AnalystTeam → multi_round_debate → TraderAgent → RiskManager → FundManager
All state is persisted in SharedState for cross-day memory.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
import yfinance as yf

from state import SharedState
from agents import (
    AnalystTeam,
    FundManager,
    RiskManager,
    TraderAgent,
    multi_round_debate,
)
from config import DEBATE_ROUNDS


class Backtest:
    """
    Simulates a TradingAgents portfolio over a historical date range.

    Parameters
    ----------
    symbol : str
        Ticker symbol (e.g. "AAPL").
    start_date : str
        ISO date string "YYYY-MM-DD".
    end_date : str
        ISO date string "YYYY-MM-DD".
    initial_capital : float
        Starting cash in USD.
    debate_rounds : int
        Number of bull/bear debate rounds per trading day.
    verbose : bool
        If True, prints agent decisions to stdout.
    """

    def __init__(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        initial_capital: float = 100_000.0,
        debate_rounds: int = DEBATE_ROUNDS,
        verbose: bool = True,
        logger_func: callable = print,
    ) -> None:
        self.symbol = symbol.upper()
        self.start = pd.to_datetime(start_date)
        self.end = pd.to_datetime(end_date)
        self.initial_capital = initial_capital
        self.debate_rounds = debate_rounds
        self.verbose = verbose
        self.logger = logger_func

        # Runtime state
        self.state = SharedState()
        self.cash = initial_capital
        self.positions = 0.0  # shares held
        self.trades: list[tuple] = []  # (date_str, action, shares, price)
        self.portfolio_series: pd.Series | None = None

    # -- Public API ------------------------------------------------------------

    def fetch_prices(self) -> pd.Series:
        df = yf.download(
            self.symbol, start=self.start, end=self.end, progress=False, auto_adjust=True
        )
        if df.empty:
            raise ValueError(f"No price data returned for {self.symbol} in the requested range.")
        
        # Ensure we always have a Series, even if it's 1 row
        prices = df["Close"]
        if isinstance(prices, pd.DataFrame):
            prices = prices.iloc[:, 0]
        
        return prices.dropna()

    def run(self) -> pd.Series:
        """Execute the backtest. Returns a pd.Series of daily portfolio values."""
        prices = self.fetch_prices()
        portfolio = pd.Series(index=prices.index, dtype=float)
        self.cash = self.initial_capital
        self.positions = 0.0

        for date, price in prices.items():
            date_str = date.strftime("%Y-%m-%d")
            price = float(price)

            if self.verbose:
                self.logger(f"\n{'='*40}")
                self.logger(f"[DATE] {date_str} | Price: ${price:.2f}")
                self.logger(f"{'='*40}")

            # 1. Analyst Team (with memory from prior days)
            past_reports = self.state.get_recent_analyst_reports(self.symbol, days=3)
            reports = AnalystTeam(self.symbol, reference_date=date_str, memory=past_reports).reports()
            self.state.add_analyst_report(self.symbol, date_str, reports)

            if self.verbose:
                self.logger(f"[TECH] Price ${reports['technical'].get('price')}, RSI {reports['technical'].get('RSI_14')}")
                self.logger(f"[SENT] score: {reports['sentiment'].get('score', 'N/A')}")

            # 2. Multi-round Bull/Bear Debate
            debate_summary = multi_round_debate(
                reports, self.state, self.symbol, date_str, rounds=self.debate_rounds
            )
            if self.verbose:
                self.logger(f"[DEBATE] Verdict: {debate_summary[:150]}...")

            # 3. Trader proposes a trade
            trade_proposal = TraderAgent(debate_summary).propose()
            if self.verbose:
                self.logger(f"[TRADE] Action: {trade_proposal.get('action')} ({trade_proposal.get('percentage')}%)")

            # 4. Risk manager scales the position
            risk_factor = RiskManager(trade_proposal).adjust()

            # 5. Fund manager finalizes
            decision = FundManager(trade_proposal, risk_factor).decide()
            if self.verbose:
                self.logger(f"[FINAL] {decision.get('action')} at {decision.get('executed_percentage')}%")
            self.state.add_trade_decision(self.symbol, date_str, decision)

            # 6. Execute trade
            self._execute(decision, price, date_str)

            portfolio[date] = self.cash + self.positions * price

        self.portfolio_series = portfolio
        return portfolio

    def metrics(self) -> dict:
        """Compute performance metrics from the completed backtest."""
        if self.portfolio_series is None or len(self.portfolio_series) < 2:
            return {
                "Cumulative Return (%)": 0.0,
                "Annualized Return (%)": 0.0,
                "Sharpe Ratio": 0.0,
                "Max Drawdown (%)": 0.0,
                "Final Value ($)": self.initial_capital,
                "Num Trades": 0,
            }

        ps = self.portfolio_series
        rets = ps.pct_change().dropna()
        cum_ret = (ps.iloc[-1] - ps.iloc[0]) / ps.iloc[0] * 100
        n_days = len(rets)
        ann_ret = ((1 + cum_ret / 100) ** (252 / n_days) - 1) * 100 if n_days > 0 else 0.0
        sharpe = (rets.mean() / rets.std() * np.sqrt(252)) if rets.std() != 0 else 0.0
        rolling_max = ps.expanding().max()
        max_dd = ((ps - rolling_max) / rolling_max).min() * 100

        return {
            "Cumulative Return (%)": round(float(cum_ret), 2),
            "Annualized Return (%)": round(float(ann_ret), 2),
            "Sharpe Ratio": round(float(sharpe), 2),
            "Max Drawdown (%)": round(float(max_dd), 2),
            "Final Value ($)": round(float(ps.iloc[-1]), 2),
            "Num Trades": len(self.trades),
        }

    def trades_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.trades, columns=["Date", "Action", "Shares", "Price"])

    # -- Private ---------------------------------------------------------------

    def _execute(self, decision: dict, price: float, date_str: str) -> None:
        action = decision.get("action", "hold")
        pct = decision.get("executed_percentage", 0.0) / 100.0

        if action == "buy" and pct > 0 and self.cash > 0:
            invest = self.cash * pct
            shares = invest / price
            self.positions += shares
            self.cash -= invest
            self.trades.append((date_str, "BUY", round(shares, 4), round(price, 2)))
            if self.verbose:
                print(f"  [BUY] {shares:.4f} shares @ ${price:.2f} (${invest:.2f})")

        elif action == "sell" and pct > 0 and self.positions > 0:
            shares_to_sell = self.positions * pct
            proceeds = shares_to_sell * price
            self.positions -= shares_to_sell
            self.cash += proceeds
            self.trades.append((date_str, "SELL", round(shares_to_sell, 4), round(price, 2)))
            if self.verbose:
                print(f"  [SELL] {shares_to_sell:.4f} shares @ ${price:.2f} (${proceeds:.2f})")

        else:
            if self.verbose:
                print(f"  [HOLD]")
