# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
# Activate virtual environment (Windows)
source venv/Scripts/activate
# or on Windows PowerShell:
venv\Scripts\Activate

# Run the Streamlit app
streamlit run app.py
```

Requires `ANTHROPIC_API_KEY` in `.env`.

## Project Structure

```
app.py                  ← Entry point (~50 lines): page config, session state defaults, step routing
ui/
  __init__.py
  shared.py             ← T dict (UI strings), CSS, shared helpers (progress, parse_json, render_header/stepper, build_ppt/zip)
  step0_sparring.py     ← Sparringspartner-Dialog (3-phase context gathering with caching)
  step1_upload.py       ← Foto Upload + LLM pipeline trigger
  step2_review.py       ← Polarity Map review & editing, PPT generation
  step3_export.py       ← Fragebogen display & export (PPT, ZIP, TXT)
llm/
  __init__.py           ← MODEL_FAST / MODEL_QUALITY constants, load_dotenv()
  context.py            ← Sparring dialog: sparring_response(), sparring_summary(), extract_context_from_dialog()
  extraction.py         ← Image analysis: compress_image(), analyze_workshop_image()
  generation.py         ← Map & questionnaire generation: generate_polarity_map(), generate_questionnaire_items()
prompts.py              ← All prompt templates (German) + build_contextual_prompt()
ppt_builder.py          ← PowerPoint generation from JSON (raw XML via lxml). Two functions: build_powerpoint() for full map, build_powerpoint_simple() for map without action steps/early warnings
models.py               ← AnalysisResult dataclass
```

## Use Cases

1. **Whiteboard-Foto Upload** (implemented) — User uploads a photo of a workshop whiteboard. The image is analyzed via vision call to extract polarity data, then a full polarity map is generated.
2. **PDF-Dokumente Upload** (planned, not yet implemented) — User uploads PDF documents as input for polarity map generation. AI should ONLY use the uploaded PDFs, NOT search the internet.

## Sparringspartner-Dialog (Step 0)

Before uploading, the user goes through a 3-phase dialog:

1. **Phase 1**: User describes the workshop context in free text
2. **Phase 2**: Model summarizes context (analytically, not as referat) + asks up to 3 targeted diagnostic questions; user answers
3. **Phase 3**: Model presents final analytical synthesis; user confirms ("Ja, Map generieren") or edits ("Nein, anpassen")

### Caching Behavior
- The sparring response from Phase 2 is cached in `st.session_state.sparring_response_text`
- On "Nein, anpassen": user returns to Phase 2 with SAME questions (no new API call). Previous answers remain editable.
- New API call ONLY if user changes their Phase 1 text and resubmits.
- This prevents confusing the user with different questions after clicking "Anpassen".

### Prompt Quality Rules (in prompts.py)
- **Sparring questions**: Each question contains only ONE thought. No double questions with "und" or dashes.
- **Workshop goal**: One question should always target the workshop goal (awareness building vs. decision-making vs. model development) unless already stated.
- **Questions are diagnostic**: They test a hypothesis or clarify something specific. NOT "tell me more about X".
- **Summary is analytical synthesis**, not a referat. Must contain at least one observation the consultant didn't explicitly state but that follows from their input.

### Context Extraction
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

The structured output that drives the PowerPoint generation. **3 items per quadrant** (not 5):

```json
{
  "pole_a": "...", "pole_b": "...",
  "gps": "Greater Purpose Statement (max 10-15 words)",
  "deeper_fear": "Deeper Fear (max 10-15 words, single thought, no 'oder')",
  "upsides_a": ["", "", ""],
  "upsides_b": ["", "", ""],
  "downsides_a": ["", "", ""],
  "downsides_b": ["", "", ""],
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

## Map Generation Quality Rules

These rules are enforced in `POLARITY_MAP_GENERATION_PROMPT` and `generation.py`:

- **Pole names are BINDING**: Take poles from the workshop extraction (pole_a_guess, pole_b_guess). May be lightly smoothed but NEVER replaced with different concepts. Workshop participants chose these poles — changing them devalues their work.
- **GPS**: Max 10-15 words. Single clear sentence. No "sowohl...als auch" constructions.
- **Deeper Fear**: Max 10-15 words. Single worst-case scenario. NO "oder", NO double thoughts.
- **Items**: Max 8-12 words each. Short, concise, slide-ready.
- **Context-specific**: When workshop context is provided, items MUST reflect the specific industry, dynamics, and stakeholder perspectives. No generic formulations.
- **3 items per quadrant** (upsides and downsides).

## PowerPoint Generation

Two PowerPoint templates exist:

| Template | File | Placeholders | Content |
|---|---|---|---|
| Simple | `__Beispielmaps_deutsch.pptx` | idx 14-21 (8 total) | Map WITHOUT action steps / early warnings |
| Full | `__Beispielmaps_deutsch_2.pptx` | idx 14-25 (14 total) | Map WITH action steps / early warnings |

Both are generated on export. User gets two download buttons: "Map herunterladen (ohne Maßnahmen)" and "Map herunterladen (mit Maßnahmen)". Both are included in the ZIP export.

### Placeholder Mapping (shared between both templates)

| JSON key | Placeholder idx | Location |
|---|---|---|
| `gps` | 14 | Top center |
| `deeper_fear` | 15 | Bottom center |
| `pole_a` / `pole_b` | 16 / 17 | Left / Right center |
| `upsides_a` / `upsides_b` | 18 / 20 | Top quadrants |
| `downsides_a` / `downsides_b` | 19 / 21 | Bottom quadrants |
| `action_steps_a` / `action_steps_b` | 22 / 24 | Far left/right top (full template only) |
| `early_warnings_a` / `early_warnings_b` | 23 / 25 | Far left/right bottom (full template only) |

Text is injected via raw XML manipulation (`lxml`) — `_make_paragraph_xml()` builds `<a:p>` elements directly rather than using python-pptx's text frame API, to avoid formatting corruption.

## Prompts Language

All prompts in `prompts.py` are in German. All LLM outputs must be in German (`"Alle Texte müssen auf Deutsch sein."`).

## Protected Files

- **models.py** — Do not modify unless explicitly requested
- **prompts.py** — Only modify specific prompt strings when explicitly requested. Never change `build_contextual_prompt()` or the overall file structure.

## Design

Design-Redesign is planned as a separate future step. Do not change the UI design until explicitly requested.

## Roadmap (in order)

1. ~~Kontext-Formular~~ → Sparringspartner-Dialog (done)
2. ~~Prompt-Verbesserung~~ — Analytical sparring, context-specific generation, shorter items (done)
3. ~~Zwei Folien-Varianten~~ — Simple + full PowerPoint (done)
4. PDF-Flow (PDF document upload as input) — NEXT
5. Design-Redesign (UI/UX overhaul)

## CSS Notes

- **Expander icon font**: Streamlit's `<summary>` element contains a `<span>` with Material Icons ligature text (e.g. `keyboard_arrow_down`). Never override `font-family` on `span` elements inside `[data-testid="stExpander"] > details > summary` — this replaces the icon font and renders the ligature text literally as visible artifacts. Only target `p` elements for font styling in expander summaries.

## Development Notes

- After every major change: `git add -A && git commit` with descriptive message
- Always test with `streamlit run app.py` before committing — must start without ImportError
- The developer uses Claude Code (Sonnet) for implementation and Claude (Opus) on claude.ai as strategy/prompt sparring partner
