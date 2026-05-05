"""
config.py – Central configuration loaded from .env
"""
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Config")

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai").lower()
DEBATE_ROUNDS: int = int(os.getenv("DEBATE_ROUNDS", "2"))

# Relaxed validation: Only warn at startup, don't crash the boot process.
if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY is missing. Ensure it is set in your environment if you plan to use OpenAI.")

if LLM_PROVIDER == "groq" and not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY is missing. Ensure it is set in your environment if you plan to use Groq.")
