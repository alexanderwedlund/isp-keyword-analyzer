# src/data/file/text.py
import streamlit as st
from typing import BinaryIO
from src.data.file.reader import FileReader

class TextFileReader(FileReader):
    """Handles text file reading."""
    
    def extract_text(self, file: BinaryIO) -> str:
        """Read text content from a plain text file."""
        try:
            return file.read().decode("utf-8")
        except Exception as e:
            st.error(f"Error reading text file: {e}")
            return ""