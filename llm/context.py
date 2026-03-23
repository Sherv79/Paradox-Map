import json
import re

import anthropic

from llm import MODEL_FAST
from models import AnalysisResult
from prompts import SPARRING_PROMPT, SPARRING_SUMMARY_PROMPT, CONTEXT_EXTRACTION_PROMPT


def sparring_response(user_input: str) -> AnalysisResult:
    """Generate a sparring response with clarifying questions based on the user's context description."""
    prompt = f"""{SPARRING_PROMPT}

--- EINGABE DES BERATERS ---
{user_input}
"""
    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=MODEL_FAST,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return AnalysisResult(success=True, message=response.content[0].text)
    except Exception as e:
        return AnalysisResult(success=False, message=f"Fehler beim Sparring: {e}")


def sparring_summary(input_1: str, input_2: str) -> AnalysisResult:
    """Generate a final context summary from the full sparring dialog."""
    prompt = SPARRING_SUMMARY_PROMPT.format(input_1=input_1, input_2=input_2)
    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=MODEL_FAST,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return AnalysisResult(success=True, message=response.content[0].text)
    except Exception as e:
        return AnalysisResult(success=False, message=f"Fehler bei der Zusammenfassung: {e}")


def extract_context_from_dialog(input_1: str, input_2: str) -> dict:
    """Extract structured context dict from the sparring dialog."""
    prompt = CONTEXT_EXTRACTION_PROMPT.format(input_1=input_1, input_2=input_2)
    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=MODEL_FAST,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        # Strip markdown fences if present
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text.strip())
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
        return json.loads(text)
    except Exception:
        return {
            "branche": "",
            "hierarchieebene": "",
            "teilnehmer_anzahl": 0,
            "anlass": input_1[:200],
            "zusatzkontext": input_2[:500],
        }
