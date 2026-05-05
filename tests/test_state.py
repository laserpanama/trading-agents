"""
test_state.py – Unit tests for SharedState persistent memory.
"""
import pytest

from state import SharedState


@pytest.fixture
def state():
    return SharedState()


class TestAnalystReports:
    def test_add_and_retrieve_report(self, state):
        report = {"technical": {"price": 150.0, "RSI_14": 55.0}, "sentiment": {"score": 0.3}}
        state.add_analyst_report("AAPL", "2024-01-15", report)

        recent = state.get_recent_analyst_reports("AAPL", days=5)
        assert len(recent) == 1
        assert recent[0]["date"] == "2024-01-15"
        assert recent[0]["report"]["technical"]["price"] == 150.0

    def test_recent_reports_limits(self, state):
        for i in range(10):
            state.add_analyst_report("AAPL", f"2024-01-{i+1:02d}", {"day": i})

        recent = state.get_recent_analyst_reports("AAPL", days=3)
        assert len(recent) == 3
        assert recent[0]["report"]["day"] == 7  # 8th entry (0-indexed)

    def test_empty_reports(self, state):
        assert state.get_recent_analyst_reports("UNKNOWN") == []


class TestDebateHistory:
    def test_add_and_retrieve_debate(self, state):
        state.add_debate(
            "TSLA", "2024-02-01",
            bull="Strong EV demand growth.",
            bear="Margins declining, competition rising.",
            summary="Hold with medium confidence.",
        )

        summary = state.get_last_debate_summary("TSLA")
        assert "Hold" in summary

    def test_last_debate_empty(self, state):
        assert state.get_last_debate_summary("NVDA") == "No previous debate on record."

    def test_multiple_debates_returns_latest(self, state):
        state.add_debate("AAPL", "2024-01-01", "bull1", "bear1", "summary_old")
        state.add_debate("AAPL", "2024-01-02", "bull2", "bear2", "summary_new")

        assert state.get_last_debate_summary("AAPL") == "summary_new"


class TestTradeDecisions:
    def test_add_trade_decision(self, state):
        decision = {"action": "buy", "executed_percentage": 15.0, "risk_factor_applied": 0.75}
        state.add_trade_decision("GOOG", "2024-03-01", decision)

        decisions = state.trade_decisions["GOOG"]
        assert len(decisions) == 1
        assert decisions[0]["action"] == "buy"
        assert decisions[0]["date"] == "2024-03-01"

    def test_initial_capital(self, state):
        assert state.initial_capital == 100_000.0


class TestAgentIntegration:
    """Tests that simulate the full agent pipeline flow through SharedState."""

    def test_full_pipeline_flow(self, state):
        symbol = "MSFT"

        # Step 1: Analyst report
        state.add_analyst_report(symbol, "2024-01-15", {
            "technical": {"price": 380.0, "RSI_14": 62.0, "SMA_20": 375.0},
            "sentiment": {"score": 0.45},
            "fundamentals": {"pe_ttm": 35.2},
        })

        # Step 2: Debate
        state.add_debate(
            symbol, "2024-01-15",
            bull="Strong cloud revenue growth, AI tailwinds.",
            bear="Elevated valuation, regulatory risks.",
            summary="Buy with medium confidence.",
        )

        # Step 3: Trade decision
        state.add_trade_decision(symbol, "2024-01-15", {
            "action": "buy",
            "executed_percentage": 12.5,
            "risk_factor_applied": 0.5,
        })

        # Verify full state
        assert len(state.analyst_reports[symbol]) == 1
        assert len(state.debate_history[symbol]) == 1
        assert len(state.trade_decisions[symbol]) == 1
        assert state.get_last_debate_summary(symbol) == "Buy with medium confidence."
