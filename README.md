# PolarityAid

**An AI-powered workflow tool for organizational consultants working with Polarity Mapping.**

🔗 **Live Demo:** [polarityaid.streamlit.app](https://polarityaid.streamlit.app)
📁 **Repository:** [Sherv79/Paradox-Map](https://github.com/Sherv79/Paradox-Map)

---

## The Problem

My father is an organizational consultant who runs leadership workshops using the Polarity Mapping methodology — a framework that helps organizations manage complex tensions that have no single "right" answer. Instead of choosing between *exploration vs. exploitation* or *autonomy vs. standardization*, teams learn to navigate both poles intentionally.

After each workshop, his workflow looked like this:

1. Photograph the whiteboard output
2. Upload it to ChatGPT, write a prompt, iterate manually
3. Copy the improved map into PowerPoint — **by hand**
4. Upload the PowerPoint back to ChatGPT to generate questionnaire items
5. Manually transfer those items into a third-party platform to send surveys

**Five context switches. Three manual copy-paste steps. No quality standards enforced. Every time.**

PolarityAid replaces this entire workflow with a single AI-powered pipeline.

---

## What It Does

### 1. Context Sparring
Before anything is generated, a structured 3-phase dialog collects workshop context. The AI acts as a sparring partner — it summarizes the situation analytically, asks targeted diagnostic questions (industry, hierarchy level, group dynamics, workshop goal), and produces a structured context object that is injected into every downstream prompt.

### 2. Map Generation
Upload a workshop whiteboard photo or one or more PDF documents. A two-step LLM pipeline extracts the raw polarity structure and generates a complete, assessment-ready Polarity Map including:
- Pole names (binding from workshop output)
- GPS — Greater Purpose Statement
- Deeper Fear
- Upsides and downsides per pole (4 quadrants)
- Action steps and early warning signals

### 3. Review & Edit
The consultant reviews and edits all generated content in a structured form. Nothing is locked — every field is editable before export.

### 4. PowerPoint Export
Two PowerPoint variants are generated automatically from a branded template:
- Simple map (poles + 4 quadrants)
- Full map (+ action steps + early warnings)

### 5. Questionnaire Generation
Assessment-ready Likert-scale items and open reflection questions are generated directly from the finished map — ready to distribute to workshop participants.

---

## Architecture

```
app.py                  → Streamlit entry point, session state, step routing
ui/
  step0_sparring.py     → 3-phase context dialog with response caching
  step1_upload.py       → Image/PDF upload + LLM pipeline orchestration  
  step2_review.py       → Map editing + PowerPoint generation
  step3_export.py       → Questionnaire display + ZIP export
llm/
  extraction.py         → Vision pipeline: image compression, base64, structured extraction
  generation.py         → Map + questionnaire generation with context injection
  context.py            → Sparring dialog: response, summary, context extraction
prompts.py              → All prompt templates + build_contextual_prompt()
ppt_builder.py          → PowerPoint generation via raw XML manipulation (lxml)
models.py               → AnalysisResult dataclass
```

---

## Key Technical Decisions

**Two-model strategy**
Claude Sonnet handles fast, iterative tasks (sparring dialog, image extraction). Claude Opus handles quality-critical generation (map, questionnaire items). This separates cost from quality concerns — fast feedback loops where speed matters, higher reasoning where quality matters.

**Two-step extraction pipeline**
A vision call extracts raw content from the photo into a loose JSON structure. A separate text-only call generates the full assessment-ready map from that structure. Separating these prevents the vision model from being overloaded and gives the generation model clean, structured input to reason from.

**Raw XML injection for PowerPoint**
python-pptx's native text frame API overwrites template formatting when replacing text. All content is injected directly into `<a:p>` elements via `lxml`, preserving the branded template design exactly.

**Context injection architecture**
Workshop context (industry, hierarchy level, occasion, group dynamics) is extracted as a structured dict after the sparring dialog and prepended to every downstream prompt via `build_contextual_prompt()`. This produces industry-specific language and examples throughout — not generic output.

**Sparring response caching**
The AI's clarifying questions are cached in session state. If the consultant returns to edit their answers, they see the exact same questions — no new API call, no confusing regeneration mid-dialog.

**Prompt quality rules (enforced in generation)**
- GPS: max 10–15 words, single sentence, no "sowohl...als auch" constructions
- Deeper Fear: max 10–15 words, single worst-case scenario, no "oder" double-thoughts
- Pole names are binding from workshop output — never replaced by the model
- All items: max 8–12 words, observable behavior, no negations

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| LLM | Anthropic Claude API (Sonnet + Opus) |
| PDF parsing | pdfplumber |
| Image processing | Pillow |
| PowerPoint generation | python-pptx + lxml |
| Deployment | Streamlit Cloud |

---

## Status

Working MVP — actively used by an organizational consultant in live workshops.
