import os
import sys
import platform
from pathlib import Path
from typing import Optional, List, Dict, Any
import streamlit as st

class ModelManager:
    """Manages the loading and finding of AI models."""
    
    MODEL_CONFIGS = {
        "4B": {
            "name": "Gemma 3 4B",
            "filename": "gemma-3-4b-it-q4_0.gguf",
            "description": "Smaller model (4 billion parameters) - Faster but less accurate",
            "gpu_layers": -1,  # -1 means use all layers possible
            "search_paths": [
                Path("models/gemma-3-4b-it-q4_0.gguf"),
                Path("./models/gemma-3-4b-it-q4_0.gguf"),
                Path("./gemma-3-4b-it-q4_0.gguf"),
                Path("../models/gemma-3-4b-it-q4_0.gguf"),
            ]
        },
        "12B": {
            "name": "Gemma 3 12B",
            "filename": "gemma-3-12b-it-q4_0.gguf",
            "description": "Larger model (12 billion parameters) - More accurate but slower",
            "gpu_layers": -1,  # -1 means use all layers possible
            "search_paths": [
                Path("models/gemma-3-12b-it-q4_0.gguf"),
                Path("./models/gemma-3-12b-it-q4_0.gguf"),
                Path("./gemma-3-12b-it-q4_0.gguf"),
                Path("../models/gemma-3-12b-it-q4_0.gguf"),
            ]
        }
    }
    
    @staticmethod
    def get_available_models() -> Dict[str, Dict[str, Any]]:
        """Returns a dictionary of available models with their status (available or not)."""
        
        if not st.session_state.get("ai_available", False):
            return {}

        available_models = {}
        
        for model_id, config in ModelManager.MODEL_CONFIGS.items():
            model_exists = any(path.is_file() for path in config["search_paths"])
            available_models[model_id] = {
                "name": config["name"],
                "description": config["description"],
                "available": model_exists,
                "path": next((path for path in config["search_paths"] if path.is_file()), None)
            }
            
        return available_models
    
    @staticmethod
    def find_model_file(model_id: str) -> Optional[Path]:
        """Returns a valid model path or None if the specified model is not found."""

        if not st.session_state.get("ai_available", False):
            st.error("AI functionality is disabled because the llama-cpp-python library is not installed.")
            return None

        if model_id not in ModelManager.MODEL_CONFIGS:
            st.error(f"Unknown model ID: {model_id}")
            return None
            
        config = ModelManager.MODEL_CONFIGS[model_id]
        
        for p in config["search_paths"]:
            if p.is_file():
                st.info(f"Found model {model_id} at {p.resolve()}")
                return p
        
        for p in Path('.').glob(f'**/{config["filename"]}'):
            st.info(f"Found model {model_id} at {p.resolve()}")
            return p
                
        st.error(f"Could not find {config['name']} model file. Please check that the .gguf file exists.")
        return None
    
    @staticmethod
    def load_model(model_id: str = None):
        """Load the LLM model for analysis using the specified model ID."""
        
        if not st.session_state.get("ai_available", False):
            st.error("AI functionality is disabled because the llama-cpp-python library is not installed.")
            return None
        
        if model_id is None:
            model_id = st.session_state.get("selected_model", "4B")
        
        try:
            from llama_cpp import Llama
            LLAMA_CPP_AVAILABLE = True
        except ImportError:
            st.error("The llama-cpp-python library is not installed. Please run 'pip install llama-cpp-python' to enable AI analysis.")
            return None
        
        model_path = ModelManager.find_model_file(model_id)
        if not model_path:
            return None
        
        config = ModelManager.MODEL_CONFIGS[model_id]
        gpu_layers = config.get("gpu_layers", -1)  # Default to -1 (all layers) for maximum GPU usage
            
        try:
            st.info(f"Loading {config['name']} model from {model_path.resolve()}")
            
            st.info("Attempting to use GPU acceleration. This will be much faster if successful.")
            
            try:
                llm = Llama(
                    model_path=str(model_path),
                    n_ctx=2048,
                    n_gpu_layers=gpu_layers,  # Use all GPU layers possible
                    n_threads=4,              # Limit CPU threads to avoid overload
                    verbose=True
                )
                st.success(f"{config['name']} model loaded successfully with GPU acceleration!")
                
                try:
                    test_completion = llm.create_completion(prompt="Test", max_tokens=1)
                    st.info("GPU acceleration appears to be working.")
                except Exception as test_error:
                    st.warning(f"GPU test failed: {test_error}. The model may not be using GPU acceleration effectively.")
                
            except Exception as gpu_error:
                st.warning(f"GPU loading failed: {gpu_error}. Trying CPU fallback...")
                llm = Llama(
                    model_path=str(model_path),
                    n_ctx=2048,
                    n_gpu_layers=0,  # CPU only
                    n_threads=8      # More CPU threads for CPU-only mode
                )
                st.success(f"{config['name']} model loaded successfully on CPU!")
                
            return llm
        except Exception as e:
            st.error(f"Error loading model: {e}")
            return None

    @staticmethod
    def debug_cuda_availability():
        """Check if CUDA is available and print diagnostic information without requiring PyTorch."""

        if not st.session_state.get("ai_available", False):
            st.error("AI functionality is disabled because the llama-cpp-python library is not installed.")
            return

        st.write("### GPU Diagnostics")
        
        st.warning("The most reliable way to confirm CUDA support is working is to observe GPU usage in Task Manager while running inference.")
        
        st.info(f"Operating System: {platform.system()} {platform.release()} {platform.version()}")
        
        cuda_path = os.environ.get("CUDA_PATH", "Not set")
        st.info(f"CUDA_PATH environment variable: {cuda_path}")
        
        try:
            import llama_cpp
            st.info(f"llama-cpp-python version: {llama_cpp.__version__}")
        except Exception as e:
            st.warning(f"Failed to check llama-cpp-python: {e}")
        
        st.info(f"Python version: {sys.version}")
        
        try:
            import subprocess
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
            if result.returncode == 0:
                st.success("✅ NVIDIA driver is working (nvidia-smi command successful)")
                st.success("✅ CUDA is available on this system (based on nvidia-smi)")
            else:
                st.warning("❌ nvidia-smi command failed. NVIDIA drivers may not be installed or working properly.")
        except Exception as e:
            st.warning(f"❌ Failed to run nvidia-smi: {e}")
        
        try:
            import ctypes
            try:
                cuda_dll = ctypes.CDLL("nvcuda.dll")
                st.success("✅ CUDA library found (nvcuda.dll)")
            except:
                st.warning("❌ CUDA library not found. GPU acceleration may not work.")
        except Exception:
            pass
                
        selected_model = st.session_state.get("selected_model", "None")
        st.info(f"Currently selected model: {selected_model}")
        
        st.write("### Performance Tips")
        st.markdown("""
        For optimal performance:
        
        1. The 4B model should be much faster than the 12B model
        2. Reducing n_ctx (context size) can improve performance if memory is limited
        3. Using n_gpu_layers=-1 (current setting) ensures maximum GPU utilization
        4. Make sure to close other GPU-intensive applications when running AI analysis
        """)