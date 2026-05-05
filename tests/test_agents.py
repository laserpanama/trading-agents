"""
test_agents.py – Unit tests for agent helper functions and classes.

These tests mock LLM calls to avoid API costs during CI.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from state import SharedState


# ── Test TraderAgent ──────────────────────────────────────────────────────────

class TestTraderAgent:
    @patch("agents.call_llm")
    def test_propose_returns_valid_json(self, mock_llm):
        mock_llm.return_value = '{"action": "buy", "percentage": 25}'
        from agents import TraderAgent

        proposal = TraderAgent("Buy recommendation with high confidence.").propose()
        assert proposal["action"] == "buy"
        assert proposal["percentage"] == 25

    @patch("agents.call_llm")
    def test_propose_handles_markdown_fences(self, mock_llm):
        mock_llm.return_value = '```json\n{"action": "sell", "percentage": 50}\n```'
        from agents import TraderAgent

        proposal = TraderAgent("Sell recommendation.").propose()
        assert proposal["action"] == "sell"

    @patch("agents.call_llm")
    def test_propose_fallback_on_bad_json(self, mock_llm):
        mock_llm.return_value = "This is not valid JSON at all"
        from agents import TraderAgent

        proposal = TraderAgent("Garbled output.").propose()
        assert proposal["action"] == "hold"
        assert proposal["percentage"] == 0


# ── Test RiskManager ──────────────────────────────────────────────────────────

class TestRiskManager:
    @patch("agents.call_llm")
    def test_adjust_returns_factor(self, mock_llm):
        mock_llm.return_value = '{"factor": 0.75}'
        from agents import RiskManager

        factor = RiskManager({"action": "buy", "percentage": 30}).adjust()
        assert factor == 0.75

    @patch("agents.call_llm")
    def test_adjust_fallback_on_bad_json(self, mock_llm):
        mock_llm.return_value = "not json"
        from agents import RiskManager

        factor = RiskManager({"action": "buy", "percentage": 30}).adjust()
        assert factor == 1.0  # Safe default


# ── Test FundManager ──────────────────────────────────────────────────────────

class TestFundManager:
    def test_decide_applies_risk_factor(self):
        from agents import FundManager

        fm = FundManager({"action": "buy", "percentage": 40}, risk_factor=0.5)
        decision = fm.decide()

        assert decision["action"] == "buy"
        assert decision["executed_percentage"] == 20.0
        assert decision["risk_factor_applied"] == 0.5

    def test_decide_clamps_risk_factor(self):
        from agents import FundManager

        fm = FundManager({"action": "sell", "percentage": 80}, risk_factor=1.5)
        decision = fm.decide()

        assert decision["risk_factor_applied"] == 1.0  # Clamped to max

    def test_decide_hold(self):
        from agents import FundManager

        fm = FundManager({"action": "hold", "percentage": 0}, risk_factor=1.0)
        decision = fm.decide()

        assert decision["action"] == "hold"
        assert decision["executed_percentage"] == 0.0
