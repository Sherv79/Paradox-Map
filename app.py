import json
import streamlit as st
from pathlib import Path
from PIL import Image

from llm_logic import analyze_workshop_image, generate_polarity_map
from ppt_builder import build_powerpoint
from models import AppConfig, AnalysisResult

# Path to the template — adjust if needed
TEMPLATE_PATH = Path(__file__).parent / "__Beispielmaps_deutsch_2.pptx"
OUTPUT_PATH = Path(__file__).parent / "output_polarity_map.pptx"


def get_config() -> AppConfig:
    """Return basic app configuration."""
    return AppConfig()


def main() -> None:
    """Run the Streamlit app."""
    config = get_config()

    st.set_page_config(page_title=config.app_title, layout="wide")

    st.title(config.app_title)
    st.write(
        """
    This prototype helps organizational consultants generate polarity/paradox maps
    from workshop material.

    Upload a photo of a whiteboard or flipchart from a workshop session.
    The system will extract tensions, structure them into polarity maps,
    and generate a PowerPoint slide.
    """
    )

    st.header("Upload Workshop Image")

    uploaded_file = st.file_uploader(
        "Upload a whiteboard or flipchart photo",
        type=["png", "jpg", "jpeg"],
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file)

        st.subheader("Uploaded Image")
        st.image(image, use_container_width=True)

        # ─── Step 1: Extract content from image ───
        st.subheader("Step 1: Raw Extraction")

        if "step1_result" not in st.session_state:
            st.session_state.step1_result = None
        if "step2_result" not in st.session_state:
            st.session_state.step2_result = None
        if "polarity_data" not in st.session_state:
            st.session_state.polarity_data = None

        if st.button("Analyze Image", type="primary"):
            with st.spinner("Analyzing workshop image..."):
                result = analyze_workshop_image(image)
                st.session_state.step1_result = result
                # Reset downstream state
                st.session_state.step2_result = None
                st.session_state.polarity_data = None

        if st.session_state.step1_result is not None:
            result = st.session_state.step1_result
            if result.success:
                st.text_area(
                    "Extraction (JSON)",
                    result.message,
                    height=300,
                )

                # ─── Step 2: Generate polarity map ───
                st.subheader("Step 2: Generate Assessment-Ready Polarity Map")

                if st.button("Generate Polarity Map", type="primary"):
                    with st.spinner("Generating polarity map..."):
                        step2 = generate_polarity_map(result.message)
                        st.session_state.step2_result = step2

                if st.session_state.step2_result is not None:
                    step2 = st.session_state.step2_result
                    if step2.success:
                        st.text_area(
                            "Polarity Map (JSON)",
                            step2.message,
                            height=400,
                        )

                        # Parse the JSON
                        try:
                            # Strip any markdown code fences just in case
                            clean = step2.message.strip()
                            if clean.startswith("```"):
                                clean = clean.split("\n", 1)[1]
                            if clean.endswith("```"):
                                clean = clean.rsplit("```", 1)[0]
                            polarity_data = json.loads(clean)
                            st.session_state.polarity_data = polarity_data
                        except json.JSONDecodeError as e:
                            st.error(f"Could not parse JSON: {e}")
                            st.session_state.polarity_data = None

                        # ─── Step 3: Generate PowerPoint ───
                        if st.session_state.polarity_data is not None:
                            st.subheader("Step 3: Download PowerPoint")

                            if TEMPLATE_PATH.exists():
                                if st.button("Generate PowerPoint", type="primary"):
                                    with st.spinner("Building PowerPoint..."):
                                        try:
                                            build_powerpoint(
                                                st.session_state.polarity_data,
                                                TEMPLATE_PATH,
                                                OUTPUT_PATH,
                                            )
                                            with open(OUTPUT_PATH, "rb") as f:
                                                st.download_button(
                                                    label="Download Polarity Map (.pptx)",
                                                    data=f.read(),
                                                    file_name="polarity_map.pptx",
                                                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                                )
                                            st.success("PowerPoint generated!")
                                        except Exception as e:
                                            st.error(f"Error building PowerPoint: {e}")
                            else:
                                st.warning(
                                    f"Template not found at {TEMPLATE_PATH}. "
                                    "Please place your template file in the project folder."
                                )
                    else:
                        st.error(step2.message)
            else:
                st.error(result.message)


if __name__ == "__main__":
    main()