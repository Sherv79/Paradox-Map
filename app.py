import streamlit as st

from ui.shared import CSS, T, render_header, render_stepper
from ui.step0_sparring import render_step0
from ui.step1_upload import render_step1
from ui.step2_review import render_step2
from ui.step3_export import render_step3


def main() -> None:
    st.set_page_config(
        page_title="Polarity Map",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown(CSS, unsafe_allow_html=True)

    defaults = {
        "current_step": 0,
        "workshop_context": None,
        "ctx_branche": "",
        "ctx_hierarchie": "C-Level/Vorstand",
        "ctx_teilnehmer": 0,
        "ctx_anlass": "",
        "uploaded_image": None,
        "uploaded_filename": None,
        "step2_result": None,
        "polarity_data": None,
        "form_initialized": False,
        "questionnaire_result": None,
        "questionnaire_data": None,
        "questionnaire_initialized": False,
        "ppt_simple_bytes": None,
        "ppt_full_bytes": None,
        "zip_bytes": None,
        "step1_error": None,
        "step2_error": None,
        "sparring_phase": 1,
        "sparring_input_1": "",
        "sparring_input_2": "",
        "sparring_response_text": None,
        "sparring_summary": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    step = st.session_state.current_step

    render_header()
    render_stepper(step)
    st.markdown("---")

    if step == 0:
        render_step0()
    elif step == 1:
        render_step1()
    elif step == 2:
        render_step2()
    elif step == 3:
        render_step3()


if __name__ == "__main__":
    main()
