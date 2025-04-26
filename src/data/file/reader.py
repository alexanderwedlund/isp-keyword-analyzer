from abc import ABC, abstractmethod
from typing import BinaryIO, Optional

class FileReader(ABC):
    """Abstract base class for file readers."""
    
    @abstractmethod
    def extract_text(self, file: BinaryIO) -> str:
        """Extract text from a file."""
        pass
    
    @staticmethod
    def get_reader_for_type(file_type: str) -> 'FileReader':
        """Factory method to get appropriate reader for file type."""
        if file_type == "text/plain":
            from src.data.file.text import TextFileReader
            return TextFileReader()
        elif file_type == "application/pdf":
            from src.data.file.pdf import PDFFileReader
            return PDFFileReader()
        else:
            raise ValueError(f"Unsupported file type: {file_type}")