import json
import time

import streamlit as st

from llm.generation import generate_questionnaire_items
from ui.shared import (
    T,
    TEMPLATE_PATH,
    animate_progress,
    parse_json_robust,
    render_list_inputs,
    init_questionnaire_state,
    build_ppt_bytes,
)


def render_step2() -> None:
    st.markdown(
        f'<p class="pm-section-header">{T["step2_header"]}</p>',
        unsafe_allow_html=True,
    )

    label_a = st.session_state.get("f_pole_a") or "Pol A"
    label_b = st.session_state.get("f_pole_b") or "Pol B"

    # Core card (bordered container)
    with st.container(border=True):
        st.text_input(T["field_gps"], key="f_gps")
        st.text_input(T["field_deeper_fear"], key="f_deeper_fear")
        ca, cb = st.columns(2)
        with ca:
            st.text_input(T["field_pole_a"], key="f_pole_a")
        with cb:
            st.text_input(T["field_pole_b"], key="f_pole_b")

    with st.expander(T["section_upsides"]):
        ca, cb = st.columns(2)
        with ca:
            st.markdown(f"**{label_a}**")
            render_list_inputs("upsides_a", T["label_vorteil"], 3)
        with cb:
            st.markdown(f"**{label_b}**")
            render_list_inputs("upsides_b", T["label_vorteil"], 3)

    with st.expander(T["section_downsides"]):
        ca, cb = st.columns(2)
        with ca:
            st.markdown(f"**{label_a}**")
            render_list_inputs("downsides_a", T["label_nachteil"], 3)
        with cb:
            st.markdown(f"**{label_b}**")
            render_list_inputs("downsides_b", T["label_nachteil"], 3)

    with st.expander(T["section_actions"]):
        ca, cb = st.columns(2)
        with ca:
            st.markdown(f"**{label_a}**")
            render_list_inputs("action_steps_a", T["label_massnahme"], 3)
        with cb:
            st.markdown(f"**{label_b}**")
            render_list_inputs("action_steps_b", T["label_massnahme"], 3)

    with st.expander(T["section_warnings"]):
        ca, cb = st.columns(2)
        with ca:
            st.markdown(f"**{label_a}**")
            render_list_inputs("early_warnings_a", T["label_fruehwarn"], 3)
        with cb:
            st.markdown(f"**{label_b}**")
            render_list_inputs("early_warnings_b", T["label_fruehwarn"], 3)

    if st.session_state.get("step2_error"):
        st.error(st.session_state.pop("step2_error"))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    col_ppt, col_next = st.columns(2)

    with col_ppt:
        if st.session_state.get("ppt_bytes"):
            st.download_button(
                T["btn_ppt_download"],
                data=st.session_state.ppt_bytes,
                file_name=T["ppt_filename"],
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
            )
        else:
            if not TEMPLATE_PATH.exists():
                st.caption(T["error_template"])
            elif st.button(T["btn_ppt_create"], use_container_width=True):
                with st.spinner(T["spinner_ppt"]):
                    ppt = build_ppt_bytes()
                if ppt:
                    st.session_state.ppt_bytes = ppt
                    st.rerun()
                else:
                    st.session_state.step2_error = T["error_ppt"]
                    st.rerun()

    with col_next:
        if st.button(T["btn_next_questionnaire"], type="primary", use_container_width=True):
            if st.session_state.get("questionnaire_data") is not None:
                st.session_state.current_step = 3
                st.rerun()
                return

            progress_bar = st.progress(0)
            status = st.empty()

            q_result = animate_progress(
                generate_questionnaire_items,
                (st.session_state.step2_result.message, st.session_state.get("workshop_context")),
                progress_bar, status,
                T["status_questionnaire"],
                0, 90, step_ms=220,
            )

            if not q_result.success:
                progress_bar.empty(); status.empty()
                st.session_state.step2_error = q_result.message
                st.rerun()
                return

            progress_bar.progress(100)
            status.markdown(
                f'<p class="pm-status-done">{T["success_questionnaire"]}</p>',
                unsafe_allow_html=True,
            )
            time.sleep(0.35)

            try:
                q_data = parse_json_robust(q_result.message)
                st.session_state.questionnaire_result = q_result
                st.session_state.questionnaire_data = q_data
                init_questionnaire_state(q_data)
                st.session_state.zip_bytes = None
                st.session_state.current_step = 3
                st.rerun()
            except json.JSONDecodeError:
                progress_bar.empty(); status.empty()
                st.session_state.step2_error = T["error_json"]
                st.rerun()
