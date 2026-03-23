import base64
import io

import anthropic
from PIL import Image, ImageOps

from llm import MODEL_FAST
from models import AnalysisResult
from prompts import VISION_WORKSHOP_EXTRACTION_PROMPT


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
        return AnalysisResult(success=False, message=f"Error during image analysis: {e}")
