import io
import json
import re
import threading
import time
import zipfile

import streamlit as st
from pathlib import Path

from ppt_builder import build_powerpoint, build_powerpoint_simple

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "__Beispielmaps_deutsch_2.pptx"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "output_polarity_map.pptx"
TEMPLATE_SIMPLE_PATH = Path(__file__).resolve().parent.parent / "__Beispielmaps_deutsch.pptx"
TEMPLATE_FULL_PATH = Path(__file__).resolve().parent.parent / "__Beispielmaps_deutsch_2.pptx"
OUTPUT_SIMPLE_PATH = Path(__file__).resolve().parent.parent / "output_polarity_map_simple.pptx"
OUTPUT_FULL_PATH = Path(__file__).resolve().parent.parent / "output_polarity_map_full.pptx"

# ─── UI strings (German) ──────────────────────────────────────────────────────

T = {
    "step0_label": "Kontext",
    "step1_label": "Upload",
    "step2_label": "Polarity Map",
    "step3_label": "Fragebogen",
    "upload_header": "Workshop-Foto hochladen",
    "upload_description": (
        "Laden Sie ein Foto von einem Workshop-Whiteboard oder Flipchart hoch. "
        "Das System extrahiert die Spannungsfelder und erstellt eine fertige Polarity Map."
    ),
    "upload_file_label": "Whiteboard- oder Flipchart-Foto hochladen",
    "btn_generate": "Polarity Map generieren",
    "btn_ppt_create": "PowerPoint erstellen",
    "btn_ppt_download": "PowerPoint herunterladen",
    "btn_ppt_download_simple": "Map herunterladen (ohne Maßnahmen)",
    "btn_ppt_download_full": "Map herunterladen (mit Maßnahmen)",
    "ppt_simple_filename": "polarity_map_einfach.pptx",
    "ppt_full_filename": "polarity_map_vollstaendig.pptx",
    "btn_next_questionnaire": "Weiter zu Fragebogen",
    "btn_copy_items": "Items herunterladen (.txt)",
    "btn_back": "Zurück",
    "btn_prepare_export": "Export vorbereiten",
    "btn_download_all": "Alles herunterladen",
    "step2_header": "Ergebnisse prüfen und anpassen",
    "step3_header": "Fragebogen-Items",
    "field_gps": "Übergeordnetes Ziel (GPS)",
    "field_deeper_fear": "Schlimmster Fall (Deeper Fear)",
    "field_pole_a": "Pol A — Name",
    "field_pole_b": "Pol B — Name",
    "section_upsides": "Vorteile",
    "section_downsides": "Nachteile",
    "section_actions": "Maßnahmen",
    "section_warnings": "Frühwarnsignale",
    "label_vorteil": "Vorteil",
    "label_nachteil": "Nachteil",
    "label_massnahme": "Maßnahme",
    "label_fruehwarn": "Frühwarnsignal",
    "section_closed_items": "Geschlossene Items (Likert-Skala)",
    "section_open_questions": "Offene Fragen",
    "lead_in_caption": 'Lead-in: "Basierend auf dem, was ich sehe und erlebe, würde ich sagen dass..."',
    "scale_caption": "Skala: Fast Nie | Selten | Manchmal | Oft | Fast Immer",
    "status_analyze": "Analysiere Workshop-Bild...",
    "status_extract": "Extrahiere Polaritäten...",
    "status_generate": "Generiere Polarity Map...",
    "status_questionnaire": "Generiere Fragebogen-Items...",
    "spinner_ppt": "Erstelle PowerPoint...",
    "spinner_export": "Bereite Export vor...",
    "success_generation": "✓ Polarity Map erfolgreich erstellt",
    "success_questionnaire": "✓ Fragebogen-Items erfolgreich generiert",
    "error_no_file": "Bitte zuerst ein Bild hochladen.",
    "error_json": "Das JSON konnte nicht geparst werden. Bitte versuche es nochmal.",
    "error_template": "PowerPoint-Template nicht gefunden.",
    "error_ppt": "Fehler beim Erstellen der PowerPoint",
    "error_step1": "Fehler bei der Bildanalyse",
    "error_step2": "Fehler bei der Map-Generierung",
    "ppt_filename": "polarity_map.pptx",
    "zip_filename": "paradox_map_export.zip",
    "questionnaire_filename": "fragebogen.txt",
    "context_header": "Workshop-Kontext",
    "context_description": (
        "Beschreiben Sie kurz den Kontext Ihres Workshops. "
        "Das System stellt Ihnen anschließend gezielte Rückfragen."
    ),
    "sparring_placeholder": (
        "Beschreibe kurz den Kontext: Mit wem arbeitest du, "
        "in welchem Unternehmen, was ist der Anlass?"
    ),
    "sparring_answer_placeholder": "Beantworte die Fragen hier in Freitext...",
    "btn_absenden": "Absenden",
    "btn_ja_generieren": "Ja, Map generieren",
    "btn_nein_anpassen": "Nein, anpassen",
    "status_sparring": "Analysiere Kontext...",
    "status_summary": "Erstelle Zusammenfassung...",
    "status_extract": "Extrahiere Kontext...",
    "sparring_label_input1": "Ihre Kontextbeschreibung",
    "sparring_label_input2": "Ihre Antworten auf die Rückfragen",
    "quadrant_upside_a": "Vorteile — {pole}",
    "quadrant_upside_b": "Vorteile — {pole}",
    "quadrant_downside_a": "Nachteile Überfokus — {pole}",
    "quadrant_downside_b": "Nachteile Überfokus — {pole}",
    "lead_in_export": 'Lead-in: "Basierend auf dem, was ich sehe und erlebe, würde ich sagen dass..."',
    "closed_items_header": "=== GESCHLOSSENE ITEMS ===",
    "open_questions_header": "=== OFFENE FRAGEN ===",
    "use_case_whiteboard": "Whiteboard-Foto aus Workshop",
    "use_case_pdf": "PDF-Dokumente als Grundlage",
    "pdf_upload_header": "PDF-Dokumente hochladen",
    "pdf_upload_description": (
        "Laden Sie ein oder mehrere PDF-Dokumente hoch. "
        "Das System analysiert die Texte und erstellt daraus eine Polarity Map."
    ),
    "pdf_upload_label": "PDF-Dokumente hochladen",
    "pdf_poles_header": "Optional: Pole vorgeben",
    "pdf_poles_description": (
        "Wenn Sie die Pole bereits kennen, können Sie sie hier eingeben. "
        "Sonst leitet das System sie aus den Dokumenten ab."
    ),
    "btn_skip_sparring": "Überspringen → direkt zum Upload",
    "status_pdf_extract": "Extrahiere Text aus PDFs...",
    "status_pdf_analyze": "Analysiere Dokumente...",
    "error_no_pdf": "Bitte mindestens ein PDF hochladen.",
}

# ─── CSS ──────────────────────────────────────────────────────────────────────

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&display=swap');

/* ── Override Streamlit theme vars ── */
:root {
    --primary-color: #2563EB !important;
    --primaryColor: #2563EB !important;
}

/* ── Global ── */
html, body {
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: #FFFFFF !important;
}
.stApp {
    background-color: #FFFFFF !important;
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.block-container {
    max-width: 900px !important;
    padding-top: 6rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    padding-bottom: 5rem !important;
    margin: 0 auto !important;
    background-color: #FFFFFF !important;
}
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
[data-testid="stToolbar"]   { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stHeader"]    { display: none !important; }

/* ── Fixed header bar ── */
.pm-header-bar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 60px;
    background-color: #1A1A1A;
    display: flex;
    align-items: center;
    padding: 0 2.5rem;
    z-index: 999999;
}
.pm-header-title {
    font-size: 17px;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #FFFFFF;
    font-family: 'DM Sans', sans-serif;
    margin: 0;
}

/* ── Fixed footer bar ── */
.pm-footer-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 50px;
    background-color: #1A1A1A;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2.5rem;
    z-index: 999999;
}
.pm-footer-text {
    font-size: 13px;
    color: #6B6B6B;
    font-family: 'DM Sans', sans-serif;
}

/* ── Section header ── */
.pm-section-header {
    font-size: 22px !important;
    font-weight: 700 !important;
    color: #1A1A1A !important;
    margin: 0 0 0.5rem 0 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Description / body text ── */
.pm-description {
    font-size: 14px !important;
    color: #4A4A4A !important;
    font-family: 'DM Sans', sans-serif !important;
    line-height: 1.5 !important;
    margin: 0 !important;
}

/* ── Loading status text ── */
.pm-status {
    font-size: 14px !important;
    color: #4A4A4A !important;
    font-family: 'DM Sans', sans-serif !important;
    margin: 4px 0 0 0 !important;
}
.pm-status-done {
    font-size: 14px !important;
    color: #2E7D32 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    margin: 4px 0 0 0 !important;
}

/* ── Streamlit file uploader — uploaded file name row ── */
[data-testid="stFileUploaderFile"],
[data-testid="stFileUploaderFile"] p,
[data-testid="stFileUploaderFile"] span,
[data-testid="stFileUploaderFile"] small {
    color: #1A1A1A !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: #F7F7F7 !important;
    border: 1px solid #E0E0E0 !important;
    border-radius: 8px !important;
    color: #1A1A1A !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
    padding: 10px 14px !important;
    transition: border-color 0.15s ease !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 2px rgba(37,99,235,0.12) !important;
    outline: none !important;
}
.stTextInput label p,
.stTextArea label p {
    color: #6B6B6B !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Buttons — Primary (Blue) ── */
button[data-testid="baseButton-primary"] {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    transition: background-color 0.15s ease !important;
    width: 100% !important;
}
button[data-testid="baseButton-primary"] p,
button[data-testid="baseButton-primary"] span,
button[data-testid="baseButton-primary"] div {
    color: #FFFFFF !important;
}
button[data-testid="baseButton-primary"]:hover {
    background-color: #1D4ED8 !important;
    border: none !important;
    color: #FFFFFF !important;
}
button[data-testid="baseButton-primary"]:active {
    background-color: #1D4ED8 !important;
    color: #FFFFFF !important;
}
button[data-testid="baseButton-primary"]:focus {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    box-shadow: none !important;
    outline: none !important;
}
button[data-testid="baseButton-primary"]:disabled,
button[data-testid="baseButton-primary"][disabled] {
    background-color: #93B4F7 !important;
    color: #FFFFFF !important;
    cursor: not-allowed !important;
}
/* ── kind="primary" attribute selectors (Streamlit renders both) ── */
.stButton > button[kind="primary"],
.stButton > button[kind="primary"] p,
.stButton > button[kind="primary"] span,
.stButton > button[kind="primary"] div {
    color: #FFFFFF !important;
    background-color: #2563EB !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[kind="primary"]:hover p,
.stButton > button[kind="primary"]:hover span {
    background-color: #1D4ED8 !important;
    color: #FFFFFF !important;
}

/* ── Buttons — Secondary (Dark Grey) ── */
button[data-testid="baseButton-secondary"] {
    background-color: #4A4A4A !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    transition: background-color 0.15s ease !important;
    width: 100% !important;
}
button[data-testid="baseButton-secondary"] p,
button[data-testid="baseButton-secondary"] span,
button[data-testid="baseButton-secondary"] div {
    color: #FFFFFF !important;
}
button[data-testid="baseButton-secondary"]:hover {
    background-color: #333333 !important;
    border: none !important;
    color: #FFFFFF !important;
}
button[data-testid="baseButton-secondary"]:active {
    background-color: #333333 !important;
    color: #FFFFFF !important;
}
button[data-testid="baseButton-secondary"]:focus {
    background-color: #4A4A4A !important;
    color: #FFFFFF !important;
    outline: none !important;
    box-shadow: none !important;
}

/* ── Download Buttons (dark grey by default) ── */
[data-testid="stDownloadButton"] > button {
    background-color: #4A4A4A !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    width: 100% !important;
    transition: background-color 0.15s ease !important;
}
[data-testid="stDownloadButton"] > button p,
[data-testid="stDownloadButton"] > button span,
[data-testid="stDownloadButton"] > button div {
    color: #FFFFFF !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background-color: #333333 !important;
    color: #FFFFFF !important;
    border: none !important;
}
[data-testid="stDownloadButton"] > button:focus {
    background-color: #4A4A4A !important;
    color: #FFFFFF !important;
}
/* Primary download button (blue) */
[data-testid="stDownloadButton"] > button[data-testid="baseButton-primary"] {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
}
[data-testid="stDownloadButton"] > button[data-testid="baseButton-primary"]:hover {
    background-color: #1D4ED8 !important;
    color: #FFFFFF !important;
}

/* ── Browse files button inside uploader ── */
[data-testid="stFileUploader"] button,
[data-testid="stFileUploaderDropzoneButton"] {
    background-color: #E0E0E0 !important;
    color: #1A1A1A !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: background-color 0.15s ease !important;
}
[data-testid="stFileUploader"] button:hover,
[data-testid="stFileUploaderDropzoneButton"]:hover {
    background-color: #CCCCCC !important;
    color: #1A1A1A !important;
    border: none !important;
}

/* ── Progress bar ── */
/* Outer element = track background; overflow:hidden clips the fill */
[data-testid="stProgress"] {
    background-color: #DCFCE7 !important;
    border-radius: 6px !important;
    overflow: hidden !important;
    height: 8px !important;
    display: block !important;
}
/* Make every wrapper div inside transparent so only the fill div shows colour */
[data-testid="stProgress"] > div {
    background-color: transparent !important;
    height: 100% !important;
}
/* Fill — target every plausible depth in Streamlit 1.x */
[data-testid="stProgress"] > div > div,
[data-testid="stProgress"] > div > div > div,
[data-testid="stProgress"] > div > div > div > div {
    background-color: #22C55E !important;
    border-radius: 6px !important;
    height: 100% !important;
    transition: width 0.12s linear !important;
}
/* Class-based selectors as additional override */
.stProgress > div > div > div {
    background-color: #22C55E !important;
}
.stProgress > div > div {
    background-color: #E0E0E0 !important;
}

/* ── File Uploader dropzone ── */
[data-testid="stFileUploader"] section {
    background-color: #F7F7F7 !important;
    border: 2px dashed #D0D0D0 !important;
    border-radius: 12px !important;
    padding: 2rem 1.5rem !important;
    transition: border-color 0.15s ease !important;
}
[data-testid="stFileUploader"] section:hover {
    border-color: #2563EB !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] p,
[data-testid="stFileUploaderDropzoneInstructions"] span {
    color: #4A4A4A !important;
    font-size: 14px !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    border: 1px solid #E0E0E0 !important;
    border-radius: 8px !important;
    background-color: #FFFFFF !important;
    margin-bottom: 6px !important;
}
[data-testid="stExpander"] > details > summary {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    color: #1A1A1A !important;
    font-size: 15px !important;
    padding: 12px 16px !important;
    background-color: #FFFFFF !important;
    border-radius: 8px !important;
    list-style: none !important;
    position: relative !important;
    overflow: visible !important;
}
[data-testid="stExpander"] > details > summary > span {
    position: relative !important;
    z-index: 1 !important;
    background-color: #FFFFFF !important;
}
[data-testid="stExpander"] > details > summary p,
[data-testid="stExpander"] > details > summary span {
    color: #1A1A1A !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stExpander"] > details > div {
    padding: 4px 16px 16px 16px !important;
    background-color: #FFFFFF !important;
}
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {
    color: #1A1A1A !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    margin-bottom: 6px !important;
}
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] strong {
    color: #1A1A1A !important;
    font-weight: 700 !important;
}

/* ── Bordered container (core card) ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid #E0E0E0 !important;
    border-radius: 10px !important;
    padding: 4px 0 !important;
    background-color: #FFFFFF !important;
    margin-bottom: 12px !important;
}

/* ── Captions ── */
[data-testid="stCaptionContainer"] p {
    color: #4A4A4A !important;
    font-size: 13px !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Markdown ── */
[data-testid="stMarkdownContainer"] p {
    color: #1A1A1A !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stMarkdownContainer"] strong {
    color: #1A1A1A !important;
    font-weight: 700 !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Dividers ── */
hr {
    border: none !important;
    border-top: 1px solid #E8E8E8 !important;
    margin: 1.25rem 0 !important;
}

/* ── Stepper ── */
.pm-stepper {
    display: flex;
    align-items: flex-start;
    padding: 1rem 0;
    width: 100%;
}
.pm-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    min-width: 90px;
}
.pm-dot {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
    font-family: 'DM Sans', sans-serif;
    flex-shrink: 0;
}
.pm-dot-active  { background-color: #2563EB; color: #FFFFFF; }
.pm-dot-done    { background-color: #2E7D32; color: #FFFFFF; }
.pm-dot-pending { background-color: #FFFFFF; border: 2px solid #D0D0D0; color: #AAAAAA; }
.pm-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 12px;
    font-weight: 500;
    color: #6B6B6B;
    text-align: center;
    white-space: nowrap;
}
.pm-label-active { font-weight: 700; color: #1A1A1A; }
.pm-label-done   { color: #2E7D32; }
.pm-line {
    flex: 1;
    height: 2px;
    background-color: #E0E0E0;
    margin-top: 13px;
    min-width: 30px;
}
.pm-line-done { background-color: #2563EB; }

/* ── Columns gap ── */
[data-testid="stHorizontalBlock"] {
    gap: 10px !important;
    align-items: flex-end !important;
}
</style>
"""

# ─── Data helpers ─────────────────────────────────────────────────────────────

def parse_json_robust(text: str) -> dict:
    clean = text.strip()
    clean = re.sub(r"^```(?:json)?\s*", "", clean)
    clean = re.sub(r"\s*```$", "", clean.strip())
    start = clean.find("{")
    end = clean.rfind("}")
    if start != -1 and end != -1:
        clean = clean[start : end + 1]
    return json.loads(clean)


def init_form_state(data: dict) -> None:
    if st.session_state.get("form_initialized"):
        return
    st.session_state["f_gps"] = data.get("gps", "")
    st.session_state["f_deeper_fear"] = data.get("deeper_fear", "")
    st.session_state["f_pole_a"] = data.get("pole_a", "")
    st.session_state["f_pole_b"] = data.get("pole_b", "")
    for field, count in [
        ("upsides_a", 3), ("downsides_a", 3), ("action_steps_a", 3), ("early_warnings_a", 3),
        ("upsides_b", 3), ("downsides_b", 3), ("action_steps_b", 3), ("early_warnings_b", 3),
    ]:
        items = data.get(field, [])
        for i in range(count):
            st.session_state[f"f_{field}_{i}"] = items[i] if i < len(items) else ""
    st.session_state["form_initialized"] = True


def collect_form_data() -> dict:
    return {
        "gps": st.session_state.get("f_gps", ""),
        "deeper_fear": st.session_state.get("f_deeper_fear", ""),
        "pole_a": st.session_state.get("f_pole_a", ""),
        "pole_b": st.session_state.get("f_pole_b", ""),
        "upsides_a": [st.session_state.get(f"f_upsides_a_{i}", "") for i in range(3)],
        "downsides_a": [st.session_state.get(f"f_downsides_a_{i}", "") for i in range(3)],
        "action_steps_a": [st.session_state.get(f"f_action_steps_a_{i}", "") for i in range(3)],
        "early_warnings_a": [st.session_state.get(f"f_early_warnings_a_{i}", "") for i in range(3)],
        "upsides_b": [st.session_state.get(f"f_upsides_b_{i}", "") for i in range(3)],
        "downsides_b": [st.session_state.get(f"f_downsides_b_{i}", "") for i in range(3)],
        "action_steps_b": [st.session_state.get(f"f_action_steps_b_{i}", "") for i in range(3)],
        "early_warnings_b": [st.session_state.get(f"f_early_warnings_b_{i}", "") for i in range(3)],
    }


def render_list_inputs(field: str, label: str, count: int) -> None:
    for i in range(count):
        st.text_input(
            f"{label} {i + 1}",
            key=f"f_{field}_{i}",
            label_visibility="collapsed",
        )


def init_questionnaire_state(data: dict) -> None:
    if st.session_state.get("questionnaire_initialized"):
        return
    quadrant_order = ["upside_a", "upside_b", "downside_a", "downside_b"]
    grouped: dict = {q: [] for q in quadrant_order}
    for entry in data.get("closed_items", []):
        q = entry.get("quadrant")
        if q in grouped:
            grouped[q].append(entry.get("item", ""))
    counts = {}
    for quadrant, items in grouped.items():
        counts[quadrant] = len(items)
        for i, text in enumerate(items):
            st.session_state[f"f_q_closed_{quadrant}_{i}"] = text
    st.session_state["questionnaire_closed_counts"] = counts
    open_qs = data.get("open_questions", [])
    st.session_state["questionnaire_open_count"] = len(open_qs)
    for i, text in enumerate(open_qs):
        st.session_state[f"f_q_open_{i}"] = text
    st.session_state["questionnaire_initialized"] = True


def format_questionnaire_for_export(pole_a: str, pole_b: str) -> str:
    quadrant_labels = {
        "upside_a": T["quadrant_upside_a"].format(pole=pole_a),
        "upside_b": T["quadrant_upside_b"].format(pole=pole_b),
        "downside_a": T["quadrant_downside_a"].format(pole=pole_a),
        "downside_b": T["quadrant_downside_b"].format(pole=pole_b),
    }
    counts = st.session_state.get("questionnaire_closed_counts", {})
    lines = [T["lead_in_export"], "", T["closed_items_header"], ""]
    for quadrant in ["upside_a", "upside_b", "downside_a", "downside_b"]:
        count = counts.get(quadrant, 0)
        if count == 0:
            continue
        lines.append(f"--- {quadrant_labels[quadrant]} ---")
        for i in range(count):
            text = st.session_state.get(f"f_q_closed_{quadrant}_{i}", "")
            if text:
                lines.append(f"...{text}")
        lines.append("")
    open_count = st.session_state.get("questionnaire_open_count", 0)
    if open_count > 0:
        lines += [T["open_questions_header"], ""]
        for i in range(open_count):
            text = st.session_state.get(f"f_q_open_{i}", "")
            if text:
                lines.append(f"{i + 1}. {text}")
    return "\n".join(lines)


def build_ppt_bytes() -> tuple[bytes, bytes] | None:
    """Build both simple and full PowerPoint files. Returns (simple_bytes, full_bytes) or None."""
    try:
        data = collect_form_data()
        build_powerpoint_simple(data, TEMPLATE_SIMPLE_PATH, OUTPUT_SIMPLE_PATH)
        build_powerpoint(data, TEMPLATE_FULL_PATH, OUTPUT_FULL_PATH)
        with open(OUTPUT_SIMPLE_PATH, "rb") as f:
            simple_bytes = f.read()
        with open(OUTPUT_FULL_PATH, "rb") as f:
            full_bytes = f.read()
        return simple_bytes, full_bytes
    except Exception:
        return None


def build_zip_bytes() -> bytes | None:
    simple_ppt = st.session_state.get("ppt_simple_bytes")
    full_ppt = st.session_state.get("ppt_full_bytes")
    if simple_ppt is None or full_ppt is None:
        result = build_ppt_bytes()
        if result is None:
            return None
        simple_ppt, full_ppt = result
    pole_a = st.session_state.get("f_pole_a", "Pol A") or "Pol A"
    pole_b = st.session_state.get("f_pole_b", "Pol B") or "Pol B"
    txt = format_questionnaire_for_export(pole_a, pole_b)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(T["ppt_simple_filename"], simple_ppt)
        zf.writestr(T["ppt_full_filename"], full_ppt)
        zf.writestr(T["questionnaire_filename"], txt.encode("utf-8"))
    buf.seek(0)
    return buf.read()


# ─── Progress animation ───────────────────────────────────────────────────────

def animate_progress(
    fn: callable,
    args: tuple,
    progress_bar,
    status_placeholder,
    status_msg: str,
    pct_from: int,
    pct_to: int,
    step_ms: int = 220,
) -> object:
    """Run fn(*args) in a background thread, animate progress bar on main thread."""
    result_holder: list = [None]
    done_event = threading.Event()

    def _worker():
        result_holder[0] = fn(*args)
        done_event.set()

    threading.Thread(target=_worker, daemon=True).start()

    status_placeholder.markdown(
        f'<p class="pm-status">{status_msg}</p>', unsafe_allow_html=True
    )
    pct = pct_from
    while not done_event.is_set():
        if pct < pct_to:
            pct += 1
        progress_bar.progress(pct)
        time.sleep(step_ms / 1000.0)

    return result_holder[0]


# ─── UI components ────────────────────────────────────────────────────────────

def render_header() -> None:
    st.markdown(
        '<div class="pm-header-bar">'
        '<span class="pm-header-title">POLARITY MAP</span>'
        '</div>'
        '<div class="pm-footer-bar">'
        '<span class="pm-footer-text">\u00a9 2026 Polarity Map</span>'
        '<span class="pm-footer-text">Powered by Anthropic</span>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_stepper(step: int) -> None:
    def dot_cls(s: int) -> str:
        if s < step:  return "pm-dot pm-dot-done"
        if s == step: return "pm-dot pm-dot-active"
        return "pm-dot pm-dot-pending"

    def dot_txt(s: int) -> str:
        return "\u2713" if s < step else str(s)

    def lbl_cls(s: int) -> str:
        if s < step:  return "pm-label pm-label-done"
        if s == step: return "pm-label pm-label-active"
        return "pm-label"

    def line_cls(s: int) -> str:
        return "pm-line pm-line-done" if s < step else "pm-line"

    labels = [T["step0_label"], T["step1_label"], T["step2_label"], T["step3_label"]]
    html = '<div class="pm-stepper">'
    for i, label in enumerate(labels):
        html += (
            f'<div class="pm-step">'
            f'<div class="{dot_cls(i)}">{dot_txt(i)}</div>'
            f'<span class="{lbl_cls(i)}">{label}</span>'
            f"</div>"
        )
        if i < len(labels) - 1:
            html += f'<div class="{line_cls(i)}"></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
