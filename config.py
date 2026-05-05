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

# Only require OPENAI_API_KEY when using the OpenAI provider
_provider = os.getenv("LLM_PROVIDER", "openai").lower()
if _provider == "openai" and not OPENAI_API_KEY:
    raise EnvironmentError(
        "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key.\n"
        "Alternatively, set LLM_PROVIDER=groq to use the free Groq API."
    )
