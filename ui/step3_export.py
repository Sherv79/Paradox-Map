import streamlit as st

from ui.shared import T, format_questionnaire_for_export, build_zip_bytes


def render_step3() -> None:
    st.markdown(
        f'<p class="pm-section-header">{T["step3_header"]}</p>',
        unsafe_allow_html=True,
    )

    pole_a = st.session_state.get("f_pole_a", "Pol A") or "Pol A"
    pole_b = st.session_state.get("f_pole_b", "Pol B") or "Pol B"

    quadrant_labels = {
        "upside_a":   T["quadrant_upside_a"].format(pole=pole_a),
        "upside_b":   T["quadrant_upside_b"].format(pole=pole_b),
        "downside_a": T["quadrant_downside_a"].format(pole=pole_a),
        "downside_b": T["quadrant_downside_b"].format(pole=pole_b),
    }
    counts = st.session_state.get("questionnaire_closed_counts", {})

    with st.expander(T["section_closed_items"], expanded=True):
        st.caption(T["lead_in_caption"])
        st.caption(T["scale_caption"])
        st.markdown("")
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
            st.markdown("")

    open_count = st.session_state.get("questionnaire_open_count", 0)
    if open_count > 0:
        with st.expander(T["section_open_questions"], expanded=True):
            for i in range(open_count):
                st.text_input(
                    f"Frage {i + 1}",
                    key=f"f_q_open_{i}",
                    label_visibility="collapsed",
                )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    col_txt, col_back, col_all = st.columns([2, 1.2, 2])

    with col_txt:
        txt_bytes = format_questionnaire_for_export(pole_a, pole_b).encode("utf-8")
        st.download_button(
            T["btn_copy_items"],
            data=txt_bytes,
            file_name=T["questionnaire_filename"],
            mime="text/plain",
            use_container_width=True,
        )

    with col_back:
        if st.button(T["btn_back"], use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()

    with col_all:
        if st.session_state.get("zip_bytes"):
            st.download_button(
                T["btn_download_all"],
                data=st.session_state.zip_bytes,
                file_name=T["zip_filename"],
                mime="application/zip",
                use_container_width=True,
                type="primary",
            )
        else:
            if st.button(T["btn_prepare_export"], type="primary", use_container_width=True):
                with st.spinner(T["spinner_export"]):
                    zip_data = build_zip_bytes()
                if zip_data:
                    st.session_state.zip_bytes = zip_data
                    st.rerun()
                else:
                    st.error(T["error_ppt"])
