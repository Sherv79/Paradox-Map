import base64
import io
import logging

import anthropic
import pdfplumber
from PIL import Image, ImageOps

from llm import MODEL_FAST, client
from models import AnalysisResult
from prompts import VISION_WORKSHOP_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


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

    try:
        response = client.messages.create(
            model=MODEL_FAST,
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
        logger.exception("Error during image analysis")
        return AnalysisResult(success=False, message="Fehler bei der Bildanalyse. Bitte versuchen Sie es erneut.")


MAX_PDF_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB per file


def extract_text_from_pdfs(pdf_files: list) -> str:
    """Extract text from one or more uploaded PDF files. Returns concatenated text with document separators."""
    all_texts = []
    for pdf_file in pdf_files:
        file_size = getattr(pdf_file, 'size', None)
        if file_size and file_size > MAX_PDF_SIZE_BYTES:
            filename = getattr(pdf_file, 'name', 'Unbekannt')
            all_texts.append(f"=== DOKUMENT: {filename} ===\n\n[Datei zu groß — max. 50 MB]")
            continue
        try:
            with pdfplumber.open(pdf_file) as pdf:
                doc_text = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        doc_text.append(text)
                filename = getattr(pdf_file, 'name', 'Unbekannt')
                all_texts.append(f"=== DOKUMENT: {filename} ===\n\n" + "\n\n".join(doc_text))
        except Exception as e:
            filename = getattr(pdf_file, 'name', 'Unbekannt')
            logger.exception("Error reading PDF: %s", filename)
            all_texts.append(f"=== DOKUMENT: {filename} ===\n\n[Fehler beim Lesen der Datei]")

    full_text = "\n\n".join(all_texts)

    # Truncate if too long (Claude context limit)
    max_chars = 100_000
    if len(full_text) > max_chars:
        full_text = full_text[:max_chars] + "\n\n[... Text wurde gekürzt ...]"

    return full_text


def analyze_pdf_content(pdf_text: str, custom_poles: dict | None = None) -> AnalysisResult:
    """
    Analyze extracted PDF text and identify polarity structure.
    If custom_poles provided, use them. Otherwise, derive poles from text.
    Returns JSON in the same format as analyze_workshop_image.
    """
    from prompts import PDF_ANALYSIS_PROMPT

    # Build pole instruction
    if custom_poles and custom_poles.get("pole_a") and custom_poles.get("pole_b"):
        pole_instruction = (
            f"Die Pole sind bereits festgelegt:\n"
            f"Pol A = '{custom_poles['pole_a']}'\n"
            f"Pol B = '{custom_poles['pole_b']}'\n"
            f"Verwende genau diese Pole und leite die Inhalte der Quadranten aus den Dokumenten ab."
        )
    else:
        pole_instruction = (
            "Leite die zentrale Polarität selbst aus den Dokumenten ab. "
            "Beide Pole müssen positive, legitime Logiken beschreiben."
        )

    prompt = PDF_ANALYSIS_PROMPT.format(pole_instruction=pole_instruction)

    full_prompt = f"""Hier sind die Dokumente:

{pdf_text}

---

{prompt}
"""

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=MODEL_FAST,
            max_tokens=2048,
            messages=[{"role": "user", "content": full_prompt}],
        )
        return AnalysisResult(success=True, message=response.content[0].text)
    except Exception as e:
        logger.exception("Error during PDF analysis")
        return AnalysisResult(success=False, message="Fehler bei der PDF-Analyse. Bitte versuchen Sie es erneut.")
