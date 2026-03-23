import json
import time

import streamlit as st
from PIL import Image, ImageOps

from llm.extraction import analyze_workshop_image
from llm.generation import generate_polarity_map
from ui.shared import T, animate_progress, parse_json_robust, init_form_state


def render_step1() -> None:
    st.markdown(
        f'<p class="pm-section-header">{T["upload_header"]}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="pm-description">{T["upload_description"]}</p>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        T["upload_file_label"],
        type=["png", "jpg", "jpeg"],
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        image = ImageOps.exif_transpose(Image.open(uploaded_file))
        st.session_state.uploaded_image = image
        st.session_state.uploaded_filename = uploaded_file.name

    if st.session_state.get("step1_error"):
        st.error(st.session_state.pop("step1_error"))

    # Button only appears once an image is loaded
    if st.session_state.get("uploaded_image") is None:
        return

    st.markdown("<br>", unsafe_allow_html=True)
    _, col_btn, _ = st.columns([1, 2, 1])
    with col_btn:
        if st.button(T["btn_generate"], type="primary", use_container_width=True):
            # Reset downstream state
            for key in ("step2_result", "polarity_data", "questionnaire_result",
                        "questionnaire_data", "ppt_bytes", "zip_bytes"):
                st.session_state[key] = None
            for flag in ("form_initialized", "questionnaire_initialized"):
                st.session_state[flag] = False

            progress_bar = st.progress(0)
            status = st.empty()

            # Stage 1: analyze image  (0 → 45%)
            step1_result = animate_progress(
                analyze_workshop_image,
                (st.session_state.uploaded_image,),
                progress_bar, status,
                T["status_analyze"],
                0, 45, step_ms=200,
            )

            if not step1_result.success:
                progress_bar.empty(); status.empty()
                st.session_state.step1_error = f'{T["error_step1"]}: {step1_result.message}'
                st.rerun()
                return

            # Stage 2: generate polarity map  (45 → 90%)
            step2_result = animate_progress(
                generate_polarity_map,
                (step1_result.message, st.session_state.get("workshop_context")),
                progress_bar, status,
                T["status_generate"],
                45, 90, step_ms=250,
            )

            if not step2_result.success:
                progress_bar.empty(); status.empty()
                st.session_state.step1_error = f'{T["error_step2"]}: {step2_result.message}'
                st.rerun()
                return

            progress_bar.progress(100)
            status.markdown(
                f'<p class="pm-status-done">{T["success_generation"]}</p>',
                unsafe_allow_html=True,
            )
            time.sleep(0.4)

            try:
                polarity_data = parse_json_robust(step2_result.message)
                st.session_state.step2_result = step2_result
                st.session_state.polarity_data = polarity_data
                init_form_state(polarity_data)
                st.session_state.current_step = 2
                st.rerun()
            except json.JSONDecodeError:
                progress_bar.empty(); status.empty()
                st.session_state.step1_error = T["error_json"]
                st.rerun()
