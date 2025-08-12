from dotenv import load_dotenv
import os
import anthropic
import streamlit as st
from datetime import datetime
from pathlib import Path
import re

# Load environment variables
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

# Verify API key
if not api_key:
    st.error("API key not found. Please check your .env file.")
    st.stop()

# Paths and constants
UPLOADS_DIR = Path('/workspace/uploads')
STANDARDS_PATH = Path('/workspace/standards/standards.pdf')
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp'}

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def get_response(grade_level, learning_targets):
    """Send user input to the AI model and get a response using the Messages API."""
    client = anthropic.Anthropic(api_key=api_key)  # Pass the API key
    
    # Updated prompt to generate lesson summaries instead of "I can" statements
    user_content = f"""
    ##CONTEXT##
    I'm designing a lesson summary based on specific learning targets. The learning targets outline the key objectives of the lesson.
    
    ##OBJECTIVE##
    Please provide:
    Grade level: {grade_level}
    Learning targets:
    {learning_targets}
    Generate a concise summary of what this lesson is about. The summary should:
    - Clearly explain the main concepts being covered
    - Use student-friendly language while maintaining accuracy
    - Provide a brief overview that helps students understand the purpose of the lesson
    - Avoid excessive detail or additional instructions
    
    ##STYLE##
    Educational and engaging
    
    ##TONE##
    Clear and student-friendly
    Concise but informative
    Focused on key concepts
    
    ##AUDIENCE##
    Students at the specified grade level
    
    ##FORMAT##
    A short paragraph summarizing the lesson
    """
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",  # Use a supported model
        system="You are a helpful assistant that generates lesson summaries from learning targets.",
        messages=[
            {"role": "user", "content": user_content}
        ],
        max_tokens=500,  # Increase token limit for detailed outputs
        stream=False  # Set to False unless streaming output
    )
    
    # Extract the text content from the response
    return response.content[0].text  # Correctly access the text attribute of the TextBlock


def _sanitize_filename(filename: str) -> str:
    """Create a safe filename by removing unsafe characters while preserving extension."""
    base, ext = os.path.splitext(filename)
    safe_base = re.sub(r"[^A-Za-z0-9._-]", "_", base).strip("._-") or "file"
    return f"{safe_base}{ext.lower()}"


def save_uploaded_file(uploaded_file) -> Path:
    """Persist an uploaded file to the UPLOADS_DIR with a timestamped filename."""
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
    safe_name = _sanitize_filename(uploaded_file.name)
    destination = UPLOADS_DIR / f"{timestamp}__{safe_name}"
    with open(destination, "wb") as out_file:
        out_file.write(uploaded_file.getbuffer())
    return destination


# Streamlit app UI
st.title("Math Standards Correlator")

# Create tabs for the two main functions
tab_uploads, tab_generator = st.tabs(["Assessment Uploads", "Lesson Summary Generator"])

with tab_uploads:
    st.subheader("Upload assessment question images")
    st.caption("Accepted formats: PNG, JPG, JPEG, WEBP. Files are saved to /workspace/uploads for ongoing use.")
    if STANDARDS_PATH.exists():
        st.caption(f"Using standards document: {STANDARDS_PATH}")
    else:
        st.warning("No standards document found at /workspace/standards/standards.pdf. Upload it to use for correlations.")

    uploaded_files = st.file_uploader(
        "Select one or more files",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        saved_paths = []
        for file_obj in uploaded_files:
            try:
                saved_path = save_uploaded_file(file_obj)
                saved_paths.append(saved_path)
            except Exception as exc:
                st.error(f"Failed to save {file_obj.name}: {exc}")
        if saved_paths:
            st.success(f"Saved {len(saved_paths)} file(s) to {UPLOADS_DIR}.")

    # Gallery of uploaded images
    st.markdown("**Uploaded files**")
    all_files = sorted(
        [p for p in UPLOADS_DIR.glob("*") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    image_files = [p for p in all_files if p.suffix.lower() in IMAGE_EXTENSIONS]

    if not all_files:
        st.info("No files uploaded yet.")
    else:
        # Show recent images in a responsive layout
        num_columns = 3
        cols = st.columns(num_columns)
        for idx, img_path in enumerate(image_files[:30]):
            with cols[idx % num_columns]:
                try:
                    st.image(str(img_path), caption=img_path.name, use_container_width=True)
                except Exception:
                    st.write(img_path.name)
                with open(img_path, "rb") as f:
                    st.download_button("Download", f.read(), file_name=img_path.name, key=f"dl-{img_path.name}")

        # List any non-image files (if added in future)
        other_files = [p for p in all_files if p.suffix.lower() not in IMAGE_EXTENSIONS]
        if other_files:
            st.markdown("**Other uploaded files**")
            for doc in other_files[:30]:
                st.write(doc.name)
                with open(doc, "rb") as f:
                    st.download_button("Download", f.read(), file_name=doc.name, key=f"dl-{doc.name}")

with tab_generator:
    st.subheader("Generate a summary of your lesson based on learning targets.")

    # Grade level dropdown
    grade_level = st.selectbox(
        "Select a grade level:",
        [
            "Kindergarten", "Grade 1", "Grade 2", "Grade 3", "Grade 4", 
            "Grade 5", "Grade 6", "Grade 7", "Grade 8", 
            "Algebra 1", "Geometry", "Algebra 2"
        ]
    )

    # Text input for learning targets
    learning_targets = st.text_area("Enter the learning targets for the lesson:")

    # Generate response
    if st.button("Generate"):
        if grade_level and learning_targets:
            with st.spinner("Generating lesson summary..."):
                try:
                    response = get_response(grade_level, learning_targets)
                    st.success("Lesson Summary Generated!")
                    st.text_area("Lesson Summary", value=response, height=400)
                except Exception as e:
                    st.error(f"An error occurred: {e}")
        else:
            st.warning("Please select a grade level and provide learning targets to generate a summary.")
