from dotenv import load_dotenv
import os
import anthropic
import streamlit as st

# Load environment variables
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

# Verify API key
if not api_key:
    st.error("API key not found. Please check your .env file.")
    st.stop()

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

# Streamlit app UI
st.title("Lesson Summary Generator")
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
