import base64
import io
import json
import os

from dotenv import load_dotenv
import anthropic
from PIL import Image, ImageOps

load_dotenv()

from models import AnalysisResult
from prompts import VISION_WORKSHOP_EXTRACTION_PROMPT, POLARITY_MAP_GENERATION_PROMPT, QUESTIONNAIRE_GENERATION_PROMPT

MODEL = "claude-sonnet-4-20250514"


def compress_image(image: Image.Image, max_size_bytes: int = 4_500_000) -> Image.Image:
    """Resize image until it fits within the API size limit."""
    # Apply EXIF orientation so rotated phone photos are sent upright
    image = ImageOps.exif_transpose(image)
    # Convert to RGB if necessary (e.g. RGBA PNGs)
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    # Start by scaling down large images
    max_dimension = 2048
    if max(image.size) > max_dimension:
        image.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    # Check size and keep reducing if needed
    quality = 85
    while quality > 20:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality)
        if buffer.tell() <= max_size_bytes:
            buffer.seek(0)
            return Image.open(buffer)
        quality -= 10

    # Last resort: shrink dimensions further
    for scale in [0.75, 0.5, 0.25]:
        resized = image.resize(
            (int(image.width * scale), int(image.height * scale)),
            Image.LANCZOS,
        )
        buffer = io.BytesIO()
        resized.save(buffer, format="JPEG", quality=50)
        if buffer.tell() <= max_size_bytes:
            buffer.seek(0)
            return Image.open(buffer)

    raise ValueError("Could not compress image below 5MB")


def analyze_workshop_image(image: Image.Image) -> AnalysisResult:
    """
    Step 1: Extract raw content from a workshop photo.
    Returns JSON with poles, notes, upsides, downsides.
    """
    image = compress_image(image)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    image_data = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")
    media_type = "image/jpeg"

    print("Media type:", media_type)
    print("Image length:", len(image_data))

    try:
        client = anthropic.Anthropic()

        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": VISION_WORKSHOP_EXTRACTION_PROMPT,
                        },
                    ],
                }
            ],
        )
        text = response.content[0].text
        return AnalysisResult(success=True, message=text)

    except Exception as e:
        return AnalysisResult(success=False, message=f"Error during image analysis: {e}")


def generate_polarity_map(extraction_json: str) -> AnalysisResult:
    """
    Step 2: Take raw extraction JSON and generate a full,
    assessment-ready polarity map with all fields needed for the PPT.

    Returns JSON with: pole_a, pole_b, gps, deeper_fear,
    upsides_a/b, downsides_a/b, action_steps_a/b, early_warnings_a/b
    """
    # Build the prompt: give the LLM the extraction as context
    prompt = f"""Hier ist die Rohextraktion aus einem Workshop-Foto:

{extraction_json}

---

{POLARITY_MAP_GENERATION_PROMPT}

WICHTIGE REGEL: Übernimm die Pol-Namen (pole_a_guess und pole_b_guess) aus der Rohextraktion. Du darfst die Formulierung leicht glätten, aber die inhaltliche Bedeutung MUSS erhalten bleiben. Erfinde KEINE neuen oder anderen Pole. Die Pole wurden im Workshop von den Teilnehmern erarbeitet und dürfen nicht verändert werden. Gleiches gilt für die Vorteile und Nachteile — bleibe so nah wie möglich an den Original-Notizen aus dem Workshop.

WICHTIG: Gib das Ergebnis als ein einziges valides JSON-Objekt zurueck.
Kein Markdown, keine Code-Fences, kein zusaetzlicher Text.

Verwende exakt diese JSON-Struktur:
{{
  "pole_a": "Name Pol A",
  "pole_b": "Name Pol B",
  "gps": "Greater Purpose Statement - 1 Satz",
  "deeper_fear": "Deeper Fear - 1 Satz",
  "upsides_a": ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"],
  "upsides_b": ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"],
  "downsides_a": ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"],
  "downsides_b": ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"],
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
            model=MODEL,
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


def generate_questionnaire_items(polarity_map_json: str) -> AnalysisResult:
    """
    Step 3: Generate assessment questionnaire items from the finished polarity map JSON.
    Returns JSON with closed_items (list of {quadrant, item}) and open_questions (list of str).
    """
    prompt = f"""Hier ist die fertige Polarity Map als JSON:

{polarity_map_json}

---

{QUESTIONNAIRE_GENERATION_PROMPT}
"""

    try:
        client = anthropic.Anthropic()

        response = client.messages.create(
            model=MODEL,
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