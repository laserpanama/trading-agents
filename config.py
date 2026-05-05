"""
config.py – Central configuration loaded from .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
DEBATE_ROUNDS: int = int(os.getenv("DEBATE_ROUNDS", "2"))

if not OPENAI_API_KEY:
    raise EnvironmentError(
        "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
    )
