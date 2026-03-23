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

## Project Structure

```
app.py                  ← Entry point (minimal): page config, session state, step routing
ui/
  shared.py             ← T dict (UI strings), CSS, shared helpers (progress, form state, export)
  step0_sparring.py     ← Sparringspartner-Dialog (3-phase context gathering)
  step1_upload.py       ← Foto Upload + LLM pipeline trigger
  step2_review.py       ← Polarity Map review & editing
  step3_export.py       ← Fragebogen display & export (PPT, ZIP, TXT)
llm/
  __init__.py           ← MODEL_FAST / MODEL_QUALITY constants, load_dotenv()
  context.py            ← Sparring dialog: sparring_response(), sparring_summary(), extract_context_from_dialog()
  extraction.py         ← Image analysis: compress_image(), analyze_workshop_image()
  generation.py         ← Map & questionnaire generation: generate_polarity_map(), generate_questionnaire_items()
prompts.py              ← All prompt templates (German) + build_contextual_prompt()
ppt_builder.py          ← PowerPoint generation from JSON (raw XML via lxml)
models.py               ← AnalysisResult dataclass
```

## Use Cases

1. **Whiteboard-Foto Upload** — User uploads a photo of a workshop whiteboard. The image is analyzed via vision call to extract polarity data.
2. **PDF-Dokumente Upload** — User uploads PDF documents as input for polarity map generation. *(planned, not yet implemented)*

## Sparringspartner-Dialog (Step 0)

Before uploading, the user goes through a 3-phase dialog:

1. **Phase 1**: User describes the workshop context in free text
2. **Phase 2**: Model summarizes context + asks up to 3 targeted questions; user answers
3. **Phase 3**: Model presents final summary; user confirms ("Ja, Map generieren") or edits ("Nein, anpassen")

On "Nein, anpassen", both inputs are shown pre-filled for editing — the model re-runs phases 2→3.

The final context is extracted as a structured dict (`branche`, `hierarchieebene`, `teilnehmer_anzahl`, `anlass`, `zusatzkontext`) and injected into all downstream prompts via `build_contextual_prompt()`.

## Two-Step LLM Pipeline

1. **`analyze_workshop_image(image)`** (`llm/extraction.py`) — Vision call with `VISION_WORKSHOP_EXTRACTION_PROMPT`. Compresses the image to ≤4.5MB/2048px, encodes as base64 JPEG, and sends to Claude. Returns raw JSON with `pole_a_guess`, `pole_b_guess`, `notes_left/right`, `upsides_a/b`, `downsides_a/b`.

2. **`generate_polarity_map(extraction_json, context)`** (`llm/generation.py`) — Text call using `POLARITY_MAP_GENERATION_PROMPT` with workshop context injected. Returns the full assessment-ready JSON.

Both return `AnalysisResult(success: bool, message: str)` from `models.py`.

## Model Strategy

- **`MODEL_FAST`** — Claude Sonnet (`claude-sonnet-4-20250514`) for image analysis and sparring dialog. Fast, cost-efficient.
- **`MODEL_QUALITY`** — Claude Opus (`claude-opus-4-20250514`) for polarity map and questionnaire generation. Higher quality reasoning.

Both constants are defined in `llm/__init__.py`.

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

All prompts in `prompts.py` are in German. All LLM outputs must be in German (`"Alle Texte müssen auf Deutsch sein."`). The step 2 prompt enforces this explicitly and specifies the exact JSON structure.

## Design

Design-Redesign is planned as a separate future step. Do not change the UI design until explicitly requested.

## Roadmap (in order)

1. ~~Kontext-Formular~~ → Sparringspartner-Dialog (done)
2. PDF-Flow (PDF document upload as input)
3. Prompt-Verbesserung (prompt quality improvements)
4. Design-Redesign (UI/UX overhaul)
