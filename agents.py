"""
agents.py – All LLM-powered agents + market data tools.

Agent pipeline:
  AnalystTeam  ->  multi_round_debate  ->  TraderAgent  ->  RiskManager  ->  FundManager

Each agent writes structured dicts (not raw text) to SharedState to prevent
information decay across the pipeline ("telephone effect").
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import finnhub
import numpy as np
import pandas as pd
import yfinance as yf
from openai import OpenAI
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from config import FINNHUB_API_KEY, LLM_MODEL, OPENAI_API_KEY, DEBATE_ROUNDS
from state import SharedState

# Provider switching (OpenAI or Groq)
import os
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# -- Clients -------------------------------------------------------------------

if LLM_PROVIDER == "groq":
    _openai_client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )
else:
    _openai_client = OpenAI(api_key=OPENAI_API_KEY)

_finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY) if FINNHUB_API_KEY else None
_vader = SentimentIntensityAnalyzer()


# -- LLM helper ----------------------------------------------------------------

def call_llm(
    system: str,
    user: str,
    model: str = LLM_MODEL,
    max_retries: int = 3,
    temperature: float = 0.3,
) -> str:
    """Call the OpenAI chat completions API with retry on transient errors."""
    for attempt in range(max_retries):
        try:
            resp = _openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
            )
            return resp.choices[0].message.content.strip()
        except Exception as exc:  # noqa: BLE001
            wait = 2 ** attempt
            print(f"  [LLM error attempt {attempt + 1}/{max_retries}]: {exc} – retrying in {wait}s")
            time.sleep(wait)
    return "Error: LLM call failed after retries."


# -- Market data tools ---------------------------------------------------------

def get_technical_indicators(symbol: str, reference_date: Optional[datetime] = None, lookback_days: int = 60) -> Dict:
    """Return price, SMA-20, RSI-14 for the day closest to reference_date."""
    end = reference_date or datetime.now()
    start = end - timedelta(days=lookback_days)
    df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)
    if df.empty:
        return {}

    close = df["Close"].squeeze()
    sma20 = close.rolling(20).mean().iloc[-1]
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain / loss
    rsi = (100 - (100 / (1 + rs))).iloc[-1]

    return {
        "price": round(float(close.iloc[-1]), 2),
        "SMA_20": round(float(sma20), 2),
        "RSI_14": round(float(rsi), 2),
        "above_SMA": bool(close.iloc[-1] > sma20),
    }


def get_news_sentiment(symbol: str, reference_date: Optional[datetime] = None, days_back: int = 7) -> Dict:
    """Return average VADER sentiment score for news headlines leading up to reference_date."""
    if _finnhub_client is None:
        return {"score": 0.0, "headlines": [], "note": "Finnhub key not configured."}

    end = reference_date or datetime.now()
    start = end - timedelta(days=days_back)
    end_str = end.strftime("%Y-%m-%d")
    start_str = start.strftime("%Y-%m-%d")
    try:
        news = _finnhub_client.company_news(symbol, _from=start_str, to=end_str)
        headlines = [n["headline"] for n in (news or [])[:8]]
        scores = [_vader.polarity_scores(h)["compound"] for h in headlines]
        avg_score = float(np.mean(scores)) if scores else 0.0
        return {
            "score": round(avg_score, 4),
            "headlines": headlines[:5],
        }
    except Exception as exc:  # noqa: BLE001
        return {"score": 0.0, "headlines": [], "error": str(exc)}


def get_fundamentals(symbol: str) -> Dict:
    """Return key fundamental metrics from Finnhub."""
    if _finnhub_client is None:
        return {"note": "Finnhub key not configured."}
    try:
        profile = _finnhub_client.company_profile2(symbol=symbol)
        metrics = _finnhub_client.company_basic_financials(symbol, "all")
        m = metrics.get("metric", {})
        return {
            "name": profile.get("name", symbol),
            "market_cap_B": round((profile.get("marketCapitalization", 0) or 0) / 1000, 2),
            "pe_ttm": m.get("peBasicExclExtraTTM", "N/A"),
            "52w_high": m.get("52WeekHigh", "N/A"),
            "52w_low": m.get("52WeekLow", "N/A"),
            "revenue_growth_yoy": m.get("revenueGrowthTTMYoy", "N/A"),
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


# -- Analyst Team --------------------------------------------------------------

class AnalystTeam:
    """
    Gathers technical, sentiment, and fundamental data for a symbol.
    Optionally includes recent memory (past reports) in its summary prompt.
    """

    def __init__(self, symbol: str, reference_date: Optional[str] = None, memory: Optional[List[Dict]] = None) -> None:
        self.symbol = symbol
        self.reference_date = pd.to_datetime(reference_date) if reference_date else datetime.now()
        self.memory = memory or []

    def reports(self) -> Dict:
        tech = get_technical_indicators(self.symbol, reference_date=self.reference_date)
        sent = get_news_sentiment(self.symbol, reference_date=self.reference_date)
        fund = get_fundamentals(self.symbol)  # Fundamentals are harder to get historically via free tier, keeping current for now

        # Build memory context if available
        memory_ctx = ""
        if self.memory:
            last = self.memory[-1].get("report", {})
            memory_ctx = f"Previous session data: price={last.get('technical', {}).get('price', 'N/A')}"

        raw = {
            "technical": tech,
            "sentiment": sent,
            "fundamentals": fund,
        }

        # Let an LLM summarize into a concise natural-language blurb
        prompt = (
            f"Symbol: {self.symbol}\n"
            f"Technical indicators: {json.dumps(tech)}\n"
            f"News sentiment (score -1 to 1): {json.dumps(sent)}\n"
            f"Fundamentals: {json.dumps(fund)}\n"
            f"{memory_ctx}\n"
            "Write a concise 3-sentence analyst briefing covering trend, sentiment, and valuation."
        )
        summary = call_llm("You are a senior financial analyst.", prompt)
        raw["summary"] = summary
        return raw


# -- Multi-round Bull vs Bear Debate -------------------------------------------

def multi_round_debate(
    reports: Dict,
    state: SharedState,
    symbol: str,
    current_date: str,
    rounds: int = DEBATE_ROUNDS,
) -> str:
    """
    Runs N rounds of bull vs bear argument refinement, then a facilitator
    synthesizes a final recommendation (buy / sell / hold + confidence).
    """
    prior_summary = state.get_last_debate_summary(symbol)
    bull_position = ""
    bear_position = ""

    for i in range(rounds):
        bull_prompt = (
            f"Prior debate summary: {prior_summary}\n"
            f"Analyst reports: {json.dumps(reports, default=str)}\n"
            f"Previous bear argument: {bear_position or 'None yet.'}\n"
            f"Round {i + 1}/{rounds}. Sharpen your BULLISH case in 2-3 sentences."
        )
        bull_position = call_llm("You are a bullish equity researcher.", bull_prompt)

        bear_prompt = (
            f"Prior debate summary: {prior_summary}\n"
            f"Analyst reports: {json.dumps(reports, default=str)}\n"
            f"Previous bull argument: {bull_position}\n"
            f"Round {i + 1}/{rounds}. Sharpen your BEARISH case in 2-3 sentences."
        )
        bear_position = call_llm("You are a bearish equity researcher.", bear_prompt)

    facilitator_prompt = (
        f"After {rounds} rounds of debate:\n"
        f"BULL FINAL: {bull_position}\n"
        f"BEAR FINAL: {bear_position}\n"
        "Synthesize both perspectives and deliver a final verdict: buy, sell, or hold. "
        "Include a brief rationale and a confidence level (low/medium/high)."
    )
    final_summary = call_llm("You are an impartial research facilitator.", facilitator_prompt)

    state.add_debate(symbol, current_date, bull_position, bear_position, final_summary)
    return final_summary


# -- Trader Agent --------------------------------------------------------------

class TraderAgent:
    """Converts a debate summary into a structured trade proposal (JSON)."""

    def __init__(self, debate_summary: str) -> None:
        self.debate = debate_summary

    def propose(self) -> Dict:
        prompt = (
            f"Research team verdict:\n{self.debate}\n\n"
            "Based on this, propose a trade action. "
            'Output ONLY valid JSON with keys "action" (buy/sell/hold) '
            'and "percentage" (0-100, portion of free capital to deploy).'
        )
        resp = call_llm("You are an experienced equity trader. Output only valid JSON.", prompt)
        # Strip markdown code fences if present
        resp_clean = resp.strip().strip("```json").strip("```").strip()
        try:
            return json.loads(resp_clean)
        except json.JSONDecodeError:
            print(f"  [TraderAgent] JSON parse failed: {resp_clean[:120]}")
            return {"action": "hold", "percentage": 0}


# -- Risk Manager --------------------------------------------------------------

class RiskManager:
    """Reviews a trade proposal and returns a position-size adjustment factor."""

    def __init__(self, trade_proposal: Dict) -> None:
        self.trade = trade_proposal

    def adjust(self) -> float:
        prompt = (
            f"Trade proposal: {json.dumps(self.trade)}\n"
            "Assess the risk. Should we scale down the position?\n"
            'Output ONLY valid JSON with key "factor" (0.25, 0.5, 0.75, or 1.0). '
            "1.0 = proceed as proposed; 0.5 = cut size in half."
        )
        resp = call_llm("You are a risk management officer. Output only valid JSON.", prompt)
        resp_clean = resp.strip().strip("```json").strip("```").strip()
        try:
            return float(json.loads(resp_clean).get("factor", 1.0))
        except (json.JSONDecodeError, ValueError):
            return 1.0


# -- Fund Manager --------------------------------------------------------------

class FundManager:
    """Applies the risk factor and issues the final executable trade decision."""

    def __init__(self, trade: Dict, risk_factor: float) -> None:
        self.trade = trade
        self.risk_factor = max(0.0, min(risk_factor, 1.0))

    def decide(self) -> Dict:
        action = self.trade.get("action", "hold")
        raw_pct = float(self.trade.get("percentage", 0))
        executed_pct = min(raw_pct * self.risk_factor, 100.0)
        return {
            "action": action,
            "executed_percentage": round(executed_pct, 2),
            "risk_factor_applied": self.risk_factor,
        }
