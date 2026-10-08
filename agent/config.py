# agent/config.py
import os
import sys
from pathlib import Path
from typing import Optional


def load_dotenv(dotenv_path: Optional[Path] = None) -> None:
    """Minimal standalone .env loader without external dependencies."""
    if dotenv_path is None:
        dotenv_path = Path.cwd() / ".env"
        if not dotenv_path.exists():
            dotenv_path = Path(__file__).resolve().parent.parent / ".env"

    if not dotenv_path.exists():
        return

    try:
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception as exc:
        print(f"[WARN] Failed to read .env file: {exc}", file=sys.stderr)


class Config:
    def __init__(self):
        load_dotenv()
        # Default providers: openai_compatible (works for OpenAI, DeepSeek, Groq, Ollama, OpenRouter, vLLM) or gemini
        self.provider: str = os.getenv("AI_PROVIDER", "openai").lower()
        self.api_key: str = (
            os.getenv("OPENAI_API_KEY")
            or os.getenv("DEEPSEEK_API_KEY")
            or os.getenv("GROQ_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("AI_API_KEY")
            or ""
        )
        self.base_url: str = os.getenv(
            "AI_BASE_URL",
            "https://api.openai.com/v1" if self.provider == "openai" else "http://localhost:11434/v1",
        )
        self.model: str = os.getenv("AI_MODEL", "gpt-4o-mini")
        self.temperature: float = float(os.getenv("AI_TEMPERATURE", "0.2"))
        self.max_tokens: int = int(os.getenv("AI_MAX_TOKENS", "4096"))
        self.max_iterations: int = int(os.getenv("AGENT_MAX_ITERATIONS", "15"))
        self.auto_confirm_tools: bool = os.getenv("AUTO_CONFIRM_TOOLS", "false").lower() in ("true", "1", "yes")
        self.timeout: int = int(os.getenv("HTTP_TIMEOUT", "60"))


config = Config()
