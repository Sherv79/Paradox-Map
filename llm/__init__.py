import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL_FAST = "claude-sonnet-4-6"
MODEL_QUALITY = "claude-opus-4-8"

client = anthropic.Anthropic()
