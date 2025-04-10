# file_processor.py v2.0
# This module provides functionality to process and extract text from files.

import PyPDF2
import streamlit as st

class FileProcessor:
    @staticmethod
    def extract_text_from_pdf(file):
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
    
    @staticmethod
    def read_text_file(file):
        """Read text content from a plain text file."""
        try:
            return file.read().decode("utf-8")
        except Exception as e:
            st.error(f"Error reading text file: {e}")
            return ""
