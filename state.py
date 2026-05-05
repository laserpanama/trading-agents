"""
state.py – Persistent shared memory across all agents.

All agents read from and write to this single SharedState instance,
which prevents the "telephone effect" where information degrades as it
passes through a chain of LLM calls.
"""
from typing import Dict, List


class SharedState:
    """Central memory store that all agents share throughout a backtest run."""

    def __init__(self) -> None:
        # {symbol: [{date: str, report: dict}]}
        self.analyst_reports: Dict[str, List[Dict]] = {}
        # {symbol: [{date, bull, bear, summary}]}
        self.debate_history: Dict[str, List[Dict]] = {}
        # {symbol: [{date, action, executed_percentage}]}
        self.trade_decisions: Dict[str, List[Dict]] = {}
        self.initial_capital: float = 100_000.0

    # ── Analyst reports ───────────────────────────────────────────────────────

    def add_analyst_report(self, symbol: str, report_date: str, report: Dict) -> None:
        self.analyst_reports.setdefault(symbol, []).append(
            {"date": report_date, "report": report}
        )

    def get_recent_analyst_reports(self, symbol: str, days: int = 5) -> List[Dict]:
        return self.analyst_reports.get(symbol, [])[-days:]

    # ── Debate history ────────────────────────────────────────────────────────

    def add_debate(
        self, symbol: str, date: str, bull: str, bear: str, summary: str
    ) -> None:
        self.debate_history.setdefault(symbol, []).append(
            {"date": date, "bull": bull, "bear": bear, "summary": summary}
        )

    def get_last_debate_summary(self, symbol: str) -> str:
        hist = self.debate_history.get(symbol, [])
        return hist[-1]["summary"] if hist else "No previous debate on record."

    # ── Trade decisions ───────────────────────────────────────────────────────

    def add_trade_decision(self, symbol: str, date: str, decision: Dict) -> None:
        self.trade_decisions.setdefault(symbol, []).append(
            {"date": date, **decision}
        )
