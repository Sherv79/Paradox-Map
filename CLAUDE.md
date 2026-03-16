# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
# Activate virtual environment (Windows)
source venv/Scripts/activate

# Run the Streamlit app
streamlit run app.py
```

Requires `ANTHROPIC_API_KEY` in `.env`.

## Two-Step LLM Pipeline

The core logic in `llm_logic.py` runs two sequential Claude API calls:

1. **`analyze_workshop_image(image)`** — Vision call with `VISION_WORKSHOP_EXTRACTION_PROMPT`. Compresses the image to ≤4.5MB/2048px, encodes as base64 JPEG, and sends to Claude Sonnet 4. Returns raw JSON with `pole_a_guess`, `pole_b_guess`, `notes_left/right`, `upsides_a/b`, `downsides_a/b`.

2. **`generate_polarity_map(extraction_json)`** — Text call using `POLARITY_MAP_GENERATION_PROMPT` injected into a structured prompt. Returns the full assessment-ready JSON (see schema below).

Both return `AnalysisResult(success: bool, message: str)` from `models.py`.

## JSON Schema (Step 2 Output)

The structured output that drives the PowerPoint generation:

```json
{
  "pole_a": "...", "pole_b": "...",
  "gps": "Greater Purpose Statement",
  "deeper_fear": "Deeper Fear",
  "upsides_a": ["", "", "", "", ""],
  "upsides_b": ["", "", "", "", ""],
  "downsides_a": ["", "", "", "", ""],
  "downsides_b": ["", "", "", "", ""],
  "action_steps_a": ["", "", ""],
  "action_steps_b": ["", "", ""],
  "early_warnings_a": ["", "", ""],
  "early_warnings_b": ["", "", ""],
  "facets": ["", "", ""],
  "quality_check": {
    "polbenennung_tragfaehig": true,
    "gps_df_stimmig": true,
    "parallelitaet": true,
    "diagonalitaet": true,
    "beobachtbarkeit": true
  },
  "open_assumptions": ["..."]
}
```

## PowerPoint Template Mapping

`ppt_builder.py` populates `__Beispielmaps_deutsch_2.pptx` (slide 0 only) using placeholder indices:

| JSON key | Placeholder idx | Location |
|---|---|---|
| `gps` | 14 | Top center |
| `deeper_fear` | 15 | Bottom center |
| `pole_a` / `pole_b` | 16 / 17 | Left / Right center |
| `upsides_a` / `upsides_b` | 18 / 20 | Top quadrants |
| `downsides_a` / `downsides_b` | 19 / 21 | Bottom quadrants |
| `action_steps_a` / `action_steps_b` | 22 / 24 | Far left/right top |
| `early_warnings_a` / `early_warnings_b` | 23 / 25 | Far left/right bottom |

Text is injected via raw XML manipulation (`lxml`) — `_make_paragraph_xml()` builds `<a:p>` elements directly rather than using python-pptx's text frame API, to avoid formatting corruption.

## Prompts Language

Both prompts in `prompts.py` are in German. All LLM outputs must be in German (`"Alle Texte müssen auf Deutsch sein."`). The step 2 prompt enforces this explicitly and specifies the exact JSON structure.

## Model

Both LLM calls use `claude-sonnet-4-20250514` (hardcoded as `MODEL` in `llm_logic.py`).
