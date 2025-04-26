import streamlit as st
from typing import Dict, Any, Optional
from src.data.file.reader import FileReader

def render_upload_ui() -> None:
    """Render the instructions for new users."""
    st.info("Add a new ISP or select an existing one to start analysis.")
    st.markdown("""
    ## Instructions

    1. **Add a new ISP**: Enter an ISP name and upload the document
    2. **Select a keyword**: Choose a specific keyword from the predefined list for analysis, or proceed with the default first keyword that appears in the selection menu
    3. **Classify sentences**: Mark each sentence as either:
       - **Actionable Advice (AA)**
       - **Other Information (OI)**
    4. **Use context when needed**: Toggle the Context button to view surrounding sentences (previous and next) for better understanding of how the keyword is used in its larger textual environment
    5. **Get classification assistance**: Click the Suggestion button to receive AI-driven classification recommendations and rationale
    6. **Save your progress**: You can save your session anytime
    7. **Export data**: Generate an Excel file with analysis results
    """)

def handle_file_upload(file, name: str) -> Optional[Dict[str, Any]]:
    """Handle a file upload and extract text."""
    if not file or not name:
        return None
        
    try:
        reader = FileReader.get_reader_for_type(file.type)
        text = reader.extract_text(file)
        
        if not text:
            st.error("Could not extract text from the uploaded file.")
            return None
            
        return {
            'name': name,
            'text': text,
            'analysis_results': {}
        }
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None