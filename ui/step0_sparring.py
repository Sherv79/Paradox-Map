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

    # ── Phase 1: Initial context input (or edit mode with both inputs) ────
    if phase == 1:
        editing = st.session_state.sparring_editing

        if editing:
            # Edit mode: show both previous inputs pre-filled
            input_1 = st.text_area(
                T["sparring_label_input1"],
                value=st.session_state.sparring_input_1,
                placeholder=T["sparring_placeholder"],
                height=150,
                key="sparring_edit_input_1",
            )
            st.markdown("")
            input_2 = st.text_area(
                T["sparring_label_input2"],
                value=st.session_state.sparring_input_2,
                placeholder=T["sparring_answer_placeholder"],
                height=150,
                key="sparring_edit_input_2",
            )
        else:
            input_1 = st.text_area(
                T["sparring_label_input1"],
                value=st.session_state.sparring_input_1,
                placeholder=T["sparring_placeholder"],
                height=150,
                key="sparring_fresh_input_1",
            )
            input_2 = None

        can_submit = bool(input_1 and input_1.strip())
        if editing:
            can_submit = can_submit and bool(input_2 and input_2.strip())

        st.markdown("<br>", unsafe_allow_html=True)
        _, col_btn, _ = st.columns([1, 2, 1])
        with col_btn:
            if st.button(
                T["btn_absenden"],
                type="primary",
                use_container_width=True,
                disabled=not can_submit,
            ):
                st.session_state.sparring_input_1 = input_1.strip()
                if editing and input_2:
                    st.session_state.sparring_input_2 = input_2.strip()

                # Call sparring model
                with st.spinner(T["status_sparring"]):
                    result = sparring_response(st.session_state.sparring_input_1)

                if result.success:
                    st.session_state.sparring_response = result.message
                    st.session_state.sparring_phase = 2
                    st.session_state.sparring_editing = False
                    st.rerun()
                else:
                    st.error(result.message)

    # ── Phase 2: Show model response + collect answers ────────────────────
    elif phase == 2:
        # Show user's initial input
        with st.chat_message("user"):
            st.write(st.session_state.sparring_input_1)

        # Show model's sparring response
        with st.chat_message("assistant"):
            st.write(st.session_state.sparring_response)

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
            st.write(st.session_state.sparring_response)

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
                st.session_state.sparring_phase = 1
                st.session_state.sparring_editing = True
                st.session_state.sparring_response = None
                st.session_state.sparring_summary = None
                st.rerun()
