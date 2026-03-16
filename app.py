import json
import re
import streamlit as st
from pathlib import Path
from PIL import Image, ImageOps

from llm_logic import analyze_workshop_image, generate_polarity_map, generate_questionnaire_items
from ppt_builder import build_powerpoint
from models import AppConfig

TEMPLATE_PATH = Path(__file__).parent / "__Beispielmaps_deutsch_2.pptx"
OUTPUT_PATH = Path(__file__).parent / "output_polarity_map.pptx"


def get_config() -> AppConfig:
    return AppConfig()


def _parse_json_robust(text: str) -> dict:
    """Parse JSON from LLM output, stripping markdown fences and surrounding text."""
    clean = text.strip()
    clean = re.sub(r"^```(?:json)?\s*", "", clean)
    clean = re.sub(r"\s*```$", "", clean.strip())
    start = clean.find("{")
    end = clean.rfind("}")
    if start != -1 and end != -1:
        clean = clean[start:end + 1]
    return json.loads(clean)


def _init_form_state(data: dict) -> None:
    """Seed session_state form fields from polarity_data (only on first load)."""
    if st.session_state.get("form_initialized"):
        return
    st.session_state["f_gps"] = data.get("gps", "")
    st.session_state["f_deeper_fear"] = data.get("deeper_fear", "")
    st.session_state["f_pole_a"] = data.get("pole_a", "")
    st.session_state["f_pole_b"] = data.get("pole_b", "")
    for field, count in [
        ("upsides_a", 5), ("downsides_a", 5), ("action_steps_a", 3), ("early_warnings_a", 3),
        ("upsides_b", 5), ("downsides_b", 5), ("action_steps_b", 3), ("early_warnings_b", 3),
    ]:
        items = data.get(field, [])
        for i in range(count):
            st.session_state[f"f_{field}_{i}"] = items[i] if i < len(items) else ""
    st.session_state["form_initialized"] = True


def _collect_form_data() -> dict:
    """Collect current form field values from session_state into a dict for build_powerpoint."""
    return {
        "gps": st.session_state.get("f_gps", ""),
        "deeper_fear": st.session_state.get("f_deeper_fear", ""),
        "pole_a": st.session_state.get("f_pole_a", ""),
        "pole_b": st.session_state.get("f_pole_b", ""),
        "upsides_a": [st.session_state.get(f"f_upsides_a_{i}", "") for i in range(5)],
        "downsides_a": [st.session_state.get(f"f_downsides_a_{i}", "") for i in range(5)],
        "action_steps_a": [st.session_state.get(f"f_action_steps_a_{i}", "") for i in range(3)],
        "early_warnings_a": [st.session_state.get(f"f_early_warnings_a_{i}", "") for i in range(3)],
        "upsides_b": [st.session_state.get(f"f_upsides_b_{i}", "") for i in range(5)],
        "downsides_b": [st.session_state.get(f"f_downsides_b_{i}", "") for i in range(5)],
        "action_steps_b": [st.session_state.get(f"f_action_steps_b_{i}", "") for i in range(3)],
        "early_warnings_b": [st.session_state.get(f"f_early_warnings_b_{i}", "") for i in range(3)],
    }


def _render_list_inputs(field: str, label: str, count: int) -> None:
    """Render a labeled group of text_input fields for a list field."""
    st.markdown(f"**{label}**")
    for i in range(count):
        st.text_input(
            f"{label} {i + 1}",
            key=f"f_{field}_{i}",
            label_visibility="collapsed",
        )


def _render_form(pole_a_name: str, pole_b_name: str) -> None:
    """Render the editable polarity map form organised as expanders."""
    st.subheader("Polarity Map bearbeiten")

    label_a = pole_a_name or "Pol A"
    label_b = pole_b_name or "Pol B"

    with st.expander("Übergeordnete Einstellungen", expanded=True):
        st.text_input("Übergeordnetes Ziel (GPS)", key="f_gps")
        st.text_input("Schlimmster Fall (Deeper Fear)", key="f_deeper_fear")
        col_a, col_b = st.columns(2)
        with col_a:
            st.text_input("Pol A — Name", key="f_pole_a")
        with col_b:
            st.text_input("Pol B — Name", key="f_pole_b")

    with st.expander("Vorteile", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**{label_a}**")
            _render_list_inputs("upsides_a", "Vorteil", 5)
        with col_b:
            st.markdown(f"**{label_b}**")
            _render_list_inputs("upsides_b", "Vorteil", 5)

    with st.expander("Nachteile", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**{label_a}**")
            _render_list_inputs("downsides_a", "Nachteil", 5)
        with col_b:
            st.markdown(f"**{label_b}**")
            _render_list_inputs("downsides_b", "Nachteil", 5)

    with st.expander("Maßnahmen", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**{label_a}**")
            _render_list_inputs("action_steps_a", "Maßnahme", 3)
        with col_b:
            st.markdown(f"**{label_b}**")
            _render_list_inputs("action_steps_b", "Maßnahme", 3)

    with st.expander("Frühwarnsignale", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**{label_a}**")
            _render_list_inputs("early_warnings_a", "Frühwarnsignal", 3)
        with col_b:
            st.markdown(f"**{label_b}**")
            _render_list_inputs("early_warnings_b", "Frühwarnsignal", 3)

def _init_questionnaire_state(data: dict) -> None:
    """Seed session_state questionnaire fields from questionnaire_data (only on first load)."""
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


def _format_questionnaire_for_export(pole_a: str, pole_b: str) -> str:
    """Format all questionnaire items as plain text for clipboard export."""
    quadrant_labels = {
        "upside_a": f"Vorteile — {pole_a}",
        "upside_b": f"Vorteile — {pole_b}",
        "downside_a": f"Nachteile Überfokus — {pole_a}",
        "downside_b": f"Nachteile Überfokus — {pole_b}",
    }
    counts = st.session_state.get("questionnaire_closed_counts", {})
    lines = [
        'Lead-in: "Basierend auf dem, was ich sehe und erlebe, würde ich sagen dass..."',
        "",
        "=== GESCHLOSSENE ITEMS ===",
        "",
    ]
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
        lines += ["=== OFFENE FRAGEN ===", ""]
        for i in range(open_count):
            text = st.session_state.get(f"f_q_open_{i}", "")
            if text:
                lines.append(f"{i + 1}. {text}")

    return "\n".join(lines)


def main() -> None:
    config = get_config()

    st.set_page_config(page_title=config.app_title, layout="wide")
    st.title(config.app_title)
    st.write(
        "Laden Sie ein Foto von einem Workshop-Whiteboard oder Flipchart hoch. "
        "Das System extrahiert die Spannungsfelder, strukturiert sie zur Polarity Map "
        "und erstellt eine fertige PowerPoint-Folie."
    )

    st.header("Workshop-Bild hochladen")
    uploaded_file = st.file_uploader(
        "Whiteboard- oder Flipchart-Foto hochladen",
        type=["png", "jpg", "jpeg"],
    )

    if uploaded_file is not None:
        image = ImageOps.exif_transpose(Image.open(uploaded_file))
        file_size_mb = uploaded_file.size / 1_048_576
        st.caption(f"📷 {uploaded_file.name} ({file_size_mb:.1f} MB)")
        with st.expander("Hochgeladenes Bild anzeigen", expanded=False):
            st.image(image, use_container_width=True)

        # Initialize base session state keys
        for key in ("step1_result", "step2_result", "polarity_data", "questionnaire_result", "questionnaire_data"):
            if key not in st.session_state:
                st.session_state[key] = None
        for flag in ("form_initialized", "questionnaire_initialized"):
            if flag not in st.session_state:
                st.session_state[flag] = False

        # ─── Combined generate button ───
        if st.button("Polarity Map generieren", type="primary"):
            # Reset everything including form
            st.session_state.step1_result = None
            st.session_state.step2_result = None
            st.session_state.polarity_data = None
            st.session_state["form_initialized"] = False
            st.session_state.questionnaire_result = None
            st.session_state.questionnaire_data = None
            st.session_state["questionnaire_initialized"] = False

            with st.spinner("Analysiere Workshop-Bild..."):
                step1 = analyze_workshop_image(image)
                st.session_state.step1_result = step1

            if step1.success:
                with st.spinner("Generiere Polarity Map..."):
                    step2 = generate_polarity_map(step1.message)
                    st.session_state.step2_result = step2
            else:
                st.error(step1.message)

        # ─── Debug: Step 1 raw output ───
        if st.session_state.step1_result is not None and st.session_state.step1_result.success:
            with st.expander("Debug: Rohextraktion Step 1"):
                st.text_area(
                    "Step 1 Output",
                    st.session_state.step1_result.message,
                    height=300,
                    label_visibility="collapsed",
                )

        # ─── Step 2 results ───
        if st.session_state.step2_result is not None:
            step2 = st.session_state.step2_result

            if not step2.success:
                st.error(step2.message)
            else:
                # Parse JSON (once) and seed form
                if st.session_state.polarity_data is None:
                    try:
                        polarity_data = _parse_json_robust(step2.message)
                        st.session_state.polarity_data = polarity_data
                    except json.JSONDecodeError as e:
                        st.error(
                            "Das JSON konnte nicht geparst werden. "
                            "Bitte versuche es nochmal."
                        )
                        with st.expander("Fehlerdetails"):
                            st.write(f"**Fehler:** {e}")
                            st.text_area("LLM-Ausgabe (roh)", step2.message, height=200)
                        if st.button("Nochmal versuchen", type="secondary"):
                            st.session_state.step2_result = None
                            st.session_state.polarity_data = None
                            st.session_state["form_initialized"] = False
                            st.rerun()

                if st.session_state.polarity_data is not None:
                    _init_form_state(st.session_state.polarity_data)

                    _render_form(
                        pole_a_name=st.session_state.get("f_pole_a", ""),
                        pole_b_name=st.session_state.get("f_pole_b", ""),
                    )

                    st.divider()

                    # ─── PowerPoint generation ───
                    if not TEMPLATE_PATH.exists():
                        st.warning(
                            f"Template nicht gefunden: {TEMPLATE_PATH}. "
                            "Bitte die Template-Datei in den Projektordner legen."
                        )
                    elif st.button("PowerPoint generieren", type="primary"):
                        with st.spinner("Erstelle PowerPoint..."):
                            try:
                                build_powerpoint(
                                    _collect_form_data(),
                                    TEMPLATE_PATH,
                                    OUTPUT_PATH,
                                )
                                with open(OUTPUT_PATH, "rb") as f:
                                    st.download_button(
                                        label="Polarity Map herunterladen (.pptx)",
                                        data=f.read(),
                                        file_name="polarity_map.pptx",
                                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                    )
                                st.success("PowerPoint erfolgreich erstellt!")
                            except Exception as e:
                                st.error(f"Fehler beim Erstellen der PowerPoint: {e}")

                    st.divider()

                    # ─── Questionnaire generation ───
                    st.subheader("Schritt 3: Fragebogen-Items generieren")

                    if st.button("Fragebogen-Items generieren", type="primary", key="btn_questionnaire"):
                        st.session_state.questionnaire_result = None
                        st.session_state.questionnaire_data = None
                        st.session_state["questionnaire_initialized"] = False
                        with st.spinner("Generiere Fragebogen-Items..."):
                            q_result = generate_questionnaire_items(
                                st.session_state.step2_result.message
                            )
                            st.session_state.questionnaire_result = q_result

                    if st.session_state.get("questionnaire_result") is not None:
                        q_result = st.session_state.questionnaire_result
                        if not q_result.success:
                            st.error(q_result.message)
                        else:
                            if st.session_state.get("questionnaire_data") is None:
                                try:
                                    q_data = _parse_json_robust(q_result.message)
                                    st.session_state.questionnaire_data = q_data
                                except json.JSONDecodeError as e:
                                    st.error("Fragebogen-JSON konnte nicht geparst werden. Bitte nochmal versuchen.")
                                    with st.expander("Fehlerdetails"):
                                        st.write(f"**Fehler:** {e}")
                                        st.text_area("LLM-Ausgabe", q_result.message, height=200)

                            if st.session_state.get("questionnaire_data") is not None:
                                _init_questionnaire_state(st.session_state.questionnaire_data)

                                pole_a = st.session_state.get("f_pole_a", "Pol A") or "Pol A"
                                pole_b = st.session_state.get("f_pole_b", "Pol B") or "Pol B"

                                quadrant_labels = {
                                    "upside_a": f"Vorteile — {pole_a}",
                                    "upside_b": f"Vorteile — {pole_b}",
                                    "downside_a": f"Nachteile Überfokus — {pole_a}",
                                    "downside_b": f"Nachteile Überfokus — {pole_b}",
                                }
                                counts = st.session_state.get("questionnaire_closed_counts", {})

                                with st.expander("Geschlossene Items (Likert-Skala)", expanded=True):
                                    st.caption('Lead-in: "Basierend auf dem, was ich sehe und erlebe, würde ich sagen dass..."')
                                    st.caption("Skala: Fast Nie | Selten | Manchmal | Oft | Fast Immer")
                                    for quadrant in ["upside_a", "upside_b", "downside_a", "downside_b"]:
                                        count = counts.get(quadrant, 0)
                                        if count == 0:
                                            continue
                                        st.markdown(f"**{quadrant_labels[quadrant]}**")
                                        for i in range(count):
                                            st.text_input(
                                                f"Item {i + 1}",
                                                key=f"f_q_closed_{quadrant}_{i}",
                                                label_visibility="collapsed",
                                            )

                                open_count = st.session_state.get("questionnaire_open_count", 0)
                                if open_count > 0:
                                    with st.expander("Offene Fragen", expanded=True):
                                        for i in range(open_count):
                                            st.text_input(
                                                f"Frage {i + 1}",
                                                key=f"f_q_open_{i}",
                                                label_visibility="collapsed",
                                            )

                                st.markdown("**Items exportieren**")
                                st.caption("Klicke auf das Kopier-Symbol oben rechts im Textfeld, um alle Items in die Zwischenablage zu kopieren.")
                                export_text = _format_questionnaire_for_export(pole_a, pole_b)
                                st.code(export_text, language=None)


if __name__ == "__main__":
    main()
