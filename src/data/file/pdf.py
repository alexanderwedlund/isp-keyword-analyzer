import PyPDF2
import streamlit as st
from typing import BinaryIO
from src.data.file.reader import FileReader

class PDFFileReader(FileReader):
    """Handles PDF file reading."""
    
    def extract_text(self, file: BinaryIO) -> str:
        """Extract text content from a PDF file."""
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
            return ""