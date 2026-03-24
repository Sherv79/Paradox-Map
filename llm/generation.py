import anthropic

from llm import MODEL_QUALITY
from models import AnalysisResult
from prompts import POLARITY_MAP_GENERATION_PROMPT, QUESTIONNAIRE_GENERATION_PROMPT, build_contextual_prompt


def generate_polarity_map(extraction_json: str, context: dict | None = None) -> AnalysisResult:
    """
    Step 2: Take raw extraction JSON and generate a full,
    assessment-ready polarity map with all fields needed for the PPT.

    Returns JSON with: pole_a, pole_b, gps, deeper_fear,
    upsides_a/b, downsides_a/b, action_steps_a/b, early_warnings_a/b
    """
    # Build the prompt: give the LLM the extraction as context
    generation_prompt = build_contextual_prompt(POLARITY_MAP_GENERATION_PROMPT, context)
    prompt = f"""Hier ist die Rohextraktion aus einem Workshop-Foto:

{extraction_json}

---

{generation_prompt}

KRITISCHE REGEL — POLE NICHT VERÄNDERN:
Die Pol-Namen aus der Rohextraktion (pole_a_guess und pole_b_guess) sind VERBINDLICH.
Du darfst die Formulierung leicht glätten (z.B. Grammatik korrigieren), aber du darfst die Pole NICHT durch andere Konzepte ersetzen.
Wenn die Rohextraktion "Agilität" und "Standardisierung" sagt, dann heißen die Pole "Agilität" und "Standardisierung" — NICHT "Harmonische Beziehungen" und "Klarheit und Kritikfähigkeit".
Die Pole wurden im Workshop von den Teilnehmern erarbeitet. Sie zu ändern entwertet die Workshop-Arbeit.
Gleiches gilt für die Vorteile und Nachteile — bleibe so nah wie möglich an den Original-Notizen.

WICHTIG: Gib das Ergebnis als ein einziges valides JSON-Objekt zurueck.
Kein Markdown, keine Code-Fences, kein zusaetzlicher Text.

Verwende exakt diese JSON-Struktur:
{{
  "pole_a": "Name Pol A",
  "pole_b": "Name Pol B",
  "gps": "Greater Purpose Statement - 1 Satz",
  "deeper_fear": "Deeper Fear - 1 Satz",
  "upsides_a": ["Item 1", "Item 2", "Item 3"],
  "upsides_b": ["Item 1", "Item 2", "Item 3"],
  "downsides_a": ["Item 1", "Item 2", "Item 3"],
  "downsides_b": ["Item 1", "Item 2", "Item 3"],
  "action_steps_a": ["Massnahme 1", "Massnahme 2", "Massnahme 3"],
  "action_steps_b": ["Massnahme 1", "Massnahme 2", "Massnahme 3"],
  "early_warnings_a": ["Fruehwarnsignal 1", "Fruehwarnsignal 2", "Fruehwarnsignal 3"],
  "early_warnings_b": ["Fruehwarnsignal 1", "Fruehwarnsignal 2", "Fruehwarnsignal 3"],
  "facets": ["Facette 1", "Facette 2", "Facette 3"],
  "quality_check": {{
    "polbenennung_tragfaehig": true,
    "gps_df_stimmig": true,
    "parallelitaet": true,
    "diagonalitaet": true,
    "beobachtbarkeit": true
  }},
  "open_assumptions": ["Annahme 1", "Annahme 2"]
}}

Alle Texte auf Deutsch.
"""

    try:
        client = anthropic.Anthropic()

        response = client.messages.create(
            model=MODEL_QUALITY,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        text = response.content[0].text
        return AnalysisResult(success=True, message=text)

    except Exception as e:
        return AnalysisResult(
            success=False,
            message=f"Error during polarity map generation: {e}",
        )


def generate_questionnaire_items(polarity_map_json: str, context: dict | None = None) -> AnalysisResult:
    """
    Step 3: Generate assessment questionnaire items from the finished polarity map JSON.
    Returns JSON with closed_items (list of {quadrant, item}) and open_questions (list of str).
    """
    questionnaire_prompt = build_contextual_prompt(QUESTIONNAIRE_GENERATION_PROMPT, context)
    prompt = f"""Hier ist die fertige Polarity Map als JSON:

{polarity_map_json}

---

{questionnaire_prompt}
"""

    try:
        client = anthropic.Anthropic()

        response = client.messages.create(
            model=MODEL_QUALITY,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        text = response.content[0].text
        return AnalysisResult(success=True, message=text)

    except Exception as e:
        return AnalysisResult(
            success=False,
            message=f"Fehler bei der Fragebogen-Generierung: {e}",
        )
