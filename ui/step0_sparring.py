import streamlit as st

from llm.context import sparring_response, sparring_summary, extract_context_from_dialog
from ui.shared import T


def render_step0() -> None:
    st.markdown(
        f'<p class="pm-section-header">{T["context_header"]}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="pm-description">{T["context_description"]}</p>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    phase = st.session_state.sparring_phase

    # ── Use Case selection — only in Phase 1 ───────────────────────────────
    if phase == 1:
        st.radio(
            "Wie möchten Sie die Polarity Map erstellen?",
            options=[T["use_case_whiteboard"], T["use_case_pdf"]],
            key="use_case_radio",
            horizontal=True,
        )
        if st.session_state.get("use_case_radio") == T["use_case_pdf"]:
            st.session_state.use_case = "pdf"
        else:
            st.session_state.use_case = "whiteboard"

        st.markdown("<br>", unsafe_allow_html=True)

    # ── Phase 1: Initial context input ─────────────────────────────────────
    if phase == 1:
        input_1 = st.text_area(
            T["sparring_label_input1"],
            value=st.session_state.sparring_input_1,
            placeholder=T["sparring_placeholder"],
            height=150,
            key="sparring_fresh_input_1",
        )

        can_submit = bool(input_1 and input_1.strip())

        st.markdown("<br>", unsafe_allow_html=True)
        _, col_btn, _ = st.columns([1, 2, 1])
        with col_btn:
            if st.button(
                T["btn_absenden"],
                type="primary",
                use_container_width=True,
                disabled=not can_submit,
            ):
                new_text = input_1.strip()

                # Only call API if the text actually changed
                if new_text != st.session_state.sparring_input_1 or not st.session_state.sparring_response_text:
                    with st.spinner(T["status_sparring"]):
                        result = sparring_response(new_text)

                    if not result.success:
                        st.error(result.message)
                        return

                    st.session_state.sparring_response_text = result.message
                    st.session_state.sparring_input_1 = new_text
                    # Reset phase-2 answers since questions changed
                    st.session_state.sparring_input_2 = ""
                else:
                    st.session_state.sparring_input_1 = new_text

                st.session_state.sparring_phase = 2
                st.rerun()

        # Skip sparring button — only for PDF use case
        if st.session_state.use_case == "pdf":
            st.markdown("<br>", unsafe_allow_html=True)
            _, col_skip, _ = st.columns([1, 2, 1])
            with col_skip:
                if st.button(T["btn_skip_sparring"], use_container_width=True):
                    st.session_state.workshop_context = None
                    st.session_state.current_step = 1
                    st.rerun()

    # ── Phase 2: Show cached model response + collect answers ──────────────
    elif phase == 2:
        # Show user's initial input
        with st.chat_message("user"):
            st.write(st.session_state.sparring_input_1)

        # Show cached sparring response (never a new API call here)
        with st.chat_message("assistant"):
            st.write(st.session_state.sparring_response_text)

        st.markdown("")
        input_2 = st.text_area(
            T["sparring_label_input2"],
            value=st.session_state.sparring_input_2,
            placeholder=T["sparring_answer_placeholder"],
            height=150,
            key="sparring_phase2_input_2",
        )

        can_submit = bool(input_2 and input_2.strip())

        st.markdown("<br>", unsafe_allow_html=True)
        _, col_btn, _ = st.columns([1, 2, 1])
        with col_btn:
            if st.button(
                T["btn_absenden"],
                type="primary",
                use_container_width=True,
                disabled=not can_submit,
            ):
                st.session_state.sparring_input_2 = input_2.strip()

                # Call summary model
                with st.spinner(T["status_summary"]):
                    result = sparring_summary(
                        st.session_state.sparring_input_1,
                        st.session_state.sparring_input_2,
                    )

                if result.success:
                    st.session_state.sparring_summary = result.message
                    st.session_state.sparring_phase = 3
                    st.rerun()
                else:
                    st.error(result.message)

    # ── Phase 3: Final summary + confirmation ─────────────────────────────
    elif phase == 3:
        # Show full dialog history
        with st.chat_message("user"):
            st.write(st.session_state.sparring_input_1)

        with st.chat_message("assistant"):
            st.write(st.session_state.sparring_response_text)

        with st.chat_message("user"):
            st.write(st.session_state.sparring_input_2)

        with st.chat_message("assistant"):
            st.write(st.session_state.sparring_summary)

        st.markdown("<br>", unsafe_allow_html=True)
        _, col_ja, col_nein, _ = st.columns([1, 1.5, 1.5, 1])
        with col_ja:
            if st.button(
                T["btn_ja_generieren"],
                type="primary",
                use_container_width=True,
            ):
                with st.spinner(T["status_extract"]):
                    context = extract_context_from_dialog(
                        st.session_state.sparring_input_1,
                        st.session_state.sparring_input_2,
                    )
                st.session_state.workshop_context = context
                st.session_state.current_step = 1
                st.rerun()

        with col_nein:
            if st.button(
                T["btn_nein_anpassen"],
                use_container_width=True,
            ):
                # Go back to Phase 2 — cached response stays, answers stay
                st.session_state.sparring_phase = 2
                st.session_state.sparring_summary = None
                st.rerun()
