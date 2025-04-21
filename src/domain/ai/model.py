# src/domain/ai/model.py
import os
from pathlib import Path
from typing import Optional, List
import streamlit as st

class ModelManager:
    """Manages the loading and finding of AI models."""
    
    # Standard places to look for the model if not explicitly specified
    DEFAULT_MODEL_PATHS = [
        Path("models/gemma-3-4b-it-q4_0.gguf"),
        Path("./models/gemma-3-4b-it-q4_0.gguf"),
        Path("./gemma-3-4b-it-q4_0.gguf"),
        Path("../models/gemma-3-4b-it-q4_0.gguf"),
    ]
    
    @staticmethod
    def find_model_file() -> Optional[Path]:
        """Returns a valid model path or None if no model is found."""
        for p in ModelManager.DEFAULT_MODEL_PATHS:
            if p.is_file():
                st.info(f"Found model at {p.resolve()}")
                return p
        
        # If not found in default locations, search current directory
        for p in Path('.').glob('**/*.gguf'):
            if 'gemma' in p.name.lower():
                st.info(f"Found model at {p.resolve()}")
                return p
                
        st.error("Could not find Gemma model file. Please check that the .gguf file exists.")
        return None
    
    @staticmethod
    def load_model():
        """Load the LLM model for analysis."""
        try:
            from llama_cpp import Llama
            LLAMA_CPP_AVAILABLE = True
        except ImportError:
            st.error("The llama-cpp-python library is not installed. Please run 'pip install llama-cpp-python' to enable AI analysis.")
            return None
        
        model_path = ModelManager.find_model_file()
        if not model_path:
            return None
            
        try:
            st.info(f"Loading model from {model_path.resolve()}")
            
            # First try with GPU acceleration
            try:
                llm = Llama(
                    model_path=str(model_path),
                    n_ctx=2048,
                    n_gpu_layers=20,  # Use 20 GPU layers by default (set to 0 for CPU only)
                )
                st.success("Model loaded successfully with GPU acceleration!")
            except Exception as gpu_error:
                st.warning(f"GPU loading failed: {gpu_error}. Trying CPU fallback...")
                llm = Llama(
                    model_path=str(model_path),
                    n_ctx=2048,
                    n_gpu_layers=0,  # CPU only
                )
                st.success("Model loaded successfully on CPU!")
                
            return llm
        except Exception as e:
            st.error(f"Error loading model: {e}")
            return None