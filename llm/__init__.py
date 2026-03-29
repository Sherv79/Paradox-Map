import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL_FAST = "claude-sonnet-4-20250514"
MODEL_QUALITY = "claude-opus-4-6"

client = anthropic.Anthropic()
