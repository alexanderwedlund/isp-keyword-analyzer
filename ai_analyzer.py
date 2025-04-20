# ai_analyzer.py v1.5
# This module provides AI-assisted analysis of ISP documents using a local LLM.

import os
import time
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import streamlit as st
from analyzer import Analyzer

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False

class AIAnalyzer:
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
        for p in AIAnalyzer.DEFAULT_MODEL_PATHS:
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
        if not LLAMA_CPP_AVAILABLE:
            st.error("The llama-cpp-python library is not installed. Please run 'pip install llama-cpp-python' to enable AI analysis.")
            return None
        
        model_path = AIAnalyzer.find_model_file()
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
    
    @staticmethod
    def analyze_sentence(model, sentence_data: dict, keyword: str) -> str:
        """Analyze a sentence and classify it as 'AA' or 'OI'."""
        if model is None:
            return "OI"  # Default to OI if model is not available
        
        # Extract sentence and context
        sentence = sentence_data['sentence']
        before_context = sentence_data.get('before_context', '')
        after_context = sentence_data.get('after_context', '')
        extended_before = "\n".join(sentence_data.get('extended_before_context', []))
        extended_after = "\n".join(sentence_data.get('extended_after_context', []))
        
        # Create the prompt in chat format
        prompt = f"""Classification task for Information Security Policy (ISP) analysis:

Please classify the following sentence as either:
- 'AA' (Actionable Advice): Sentences that contain sufficient information to act upon without any ambiguity.
- 'OI' (Other Information): Sentences that are ambiguous, too abstract, or lack specific instructions.

IMPORTANT: Thoroughly analyze the FULL CONTEXT before making your classification. Context often provides critical clues about whether a statement should be classified as AA or OI.

Evaluation Criteria:
1. Actionability: Can an employee take concrete, specific actions based solely on this information? AA requires clear, implementable steps.
2. Clarity: Is the information presented without ambiguity? AA statements should have precise requirements with minimal room for interpretation.
3. Contextual relevance: Does the surrounding context modify how the statement should be interpreted? A seemingly vague statement may become actionable when considered with its context.

Guidelines:
- Actionable Advice (AA): Specific, unambiguous instructions that employees can directly implement without interpretation. 
  Examples: "Passwords must not be given over the phone", "Read e-mail that does not need to be saved should be deleted"

- Other Information (OI): This includes:
  1. Ambiguous instructions (e.g., "orders must be submitted to IT in good time" - "good time" is subjective)
  2. Vague guidance (e.g., "all staff must exercise caution when using e-mail" - doesn't specify how)
  3. Abstract statements that indicate general direction but aren't directly actionable
  4. Strategic statements despite containing relevant keywords

Keyword being analyzed: {keyword}

FULL CONTEXT ANALYSIS:
Previous sentences: 
{extended_before}

Immediate previous context: 
{before_context}

TARGET SENTENCE TO CLASSIFY: "{sentence}"

Immediate following context: 
{after_context}

Following sentences:
{extended_after}

Classification Process:
1. First, examine the complete context carefully
2. Apply the evaluation criteria (actionability, clarity, contextual relevance)
3. Determine if the TARGET SENTENCE provides clear, actionable guidance when considered in its full context

Provide ONLY "AA" or "OI" as your response:"""
        
        try:
            # Using chat completion format as in the example script
            response = model.create_chat_completion(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.1,
            )
            
            # Extract response from chat completion format
            response_text = response["choices"][0]["message"]["content"].strip()
            st.text(f"Raw response: {response_text}")
            
            # Extract just AA or OI from the response
            if "AA" in response_text.upper():
                return "AA"
            else:
                return "OI"
        except Exception as e:
            st.error(f"Error in model inference: {e}")
            return "OI"
    
    @staticmethod
    def get_classification_suggestion(sentence_data: dict, keyword: str) -> dict:
        """
        Get a classification suggestion with rationale for a sentence.
        
        Returns a dictionary with 'classification' and 'rationale' fields.
        """
        # Try to use the AI analyzer if available
        try:
            # First try the AI method
            model = AIAnalyzer.load_model()
            if model:
                classification = AIAnalyzer.analyze_sentence(model, sentence_data, keyword)
                
                # Generate a rationale based on the classification
                sentence = sentence_data['sentence']
                context_before = sentence_data.get('before_context', '')
                context_after = sentence_data.get('after_context', '')
                
                # Create a prompt to get the rationale
                rationale_prompt = f"""Classification explanation task:

You previously classified this sentence as '{classification}' in an Information Security Policy.
Please explain WHY you classified it this way in 3-5 sentences. Focus on:
1. The specific language that makes it actionable or not
2. The clarity/ambiguity of instructions
3. How the context affects interpretation

Keyword being analyzed: {keyword}

Context before: {context_before}
TARGET SENTENCE: "{sentence}"
Context after: {context_after}

Your explanation (3-5 sentences):"""
                
                # Get the rationale explanation
                response = model.create_chat_completion(
                    messages=[
                        {"role": "user", "content": rationale_prompt}
                    ],
                    max_tokens=200,
                    temperature=0.2,
                )
                
                rationale = response["choices"][0]["message"]["content"].strip()
                
                return {
                    "classification": classification,
                    "rationale": rationale
                }
            
        except Exception as e:
            st.warning(f"AI analysis error: {e}. Using rule-based classification instead.")
        
        # Fallback to rule-based approach
        sentence = sentence_data['sentence'].lower()
        
        # Check for action words
        action_markers = ["must ", "shall ", "required to ", "always ", "never ", 
                          "do not ", "should ", "is prohibited", "is not permitted"]
        
        # Check for vague terms
        vague_terms = ["good time", "exercise caution", "be careful", "as appropriate",
                      "when necessary", "as needed", "reasonable", "proper"]
        
        # Check if sentence contains action markers without vague terms
        is_actionable = False
        if any(marker in sentence for marker in action_markers):
            if not any(term in sentence for term in vague_terms):
                is_actionable = True
        
        classification = "AA" if is_actionable else "OI"
        
        # Generate a simple rationale based on rule-based classification
        if classification == "AA":
            action_words = [marker for marker in action_markers if marker in sentence]
            rationale = f"This sentence contains clear action words ({', '.join(action_words)}) without ambiguous terms, making it specific enough to be actionable. The instruction is clear and provides concrete guidance that can be directly implemented."
        else:
            if any(term in sentence for term in vague_terms):
                vague_found = [term for term in vague_terms if term in sentence]
                rationale = f"Although the sentence contains the keyword '{keyword}', it uses vague terminology ({', '.join(vague_found)}) that makes the guidance ambiguous. This lack of specificity means it cannot be directly acted upon without additional interpretation."
            elif not any(marker in sentence for marker in action_markers):
                rationale = f"This sentence lacks clear action words that would make it actionable. It appears to be informational rather than providing specific guidance. Without explicit direction on what to do, it should be classified as Other Information."
            else:
                rationale = f"While the sentence contains the keyword '{keyword}', it does not provide clear, specific instructions that can be directly implemented. The statement is more informational than actionable."
        
        return {
            "classification": classification,
            "rationale": rationale
        }
    
    @staticmethod
    def simple_analyze_keyword(isp_data: Dict, keyword: str) -> Dict:
        """
        Simple rule-based classification as fallback when AI is not available.
        """
        if 'analysis_results' not in isp_data:
            isp_data['analysis_results'] = {}
        
        # Get sentences with the keyword
        sentences = Analyzer.find_sentences_with_keyword(isp_data.get('text', ''), keyword)
        
        if not sentences:
            if keyword not in isp_data['analysis_results']:
                isp_data['analysis_results'][keyword] = {'AA': [], 'OI': []}
            return isp_data
        
        if keyword not in isp_data['analysis_results']:
            isp_data['analysis_results'][keyword] = {'AA': [], 'OI': []}
        
        st.info(f"Using rule-based classification for {len(sentences)} sentences with keyword '{keyword}'")
        progress_bar = st.progress(0)
        
        aa_count = 0
        oi_count = 0
        
        for i, item in enumerate(sentences):
            sentence = item['sentence'].lower()
            is_actionable = False
            
            # Check for action words
            action_markers = ["must ", "shall ", "required to ", "always ", "never ", 
                             "do not ", "should ", "is prohibited", "is not permitted"]
            
            # Check for vague terms
            vague_terms = ["good time", "exercise caution", "be careful", "as appropriate",
                         "when necessary", "as needed", "reasonable", "proper"]
            
            # Check if sentence contains action markers without vague terms
            if any(marker in sentence for marker in action_markers):
                if not any(term in sentence for term in vague_terms):
                    is_actionable = True
            
            occurrence_id = f"{item['sentence']}::{item['start']}::{item['end']}"
            
            if is_actionable:
                aa_count += 1
                if occurrence_id not in isp_data['analysis_results'][keyword]['AA']:
                    isp_data['analysis_results'][keyword]['AA'].append(occurrence_id)
                if occurrence_id in isp_data['analysis_results'][keyword]['OI']:
                    isp_data['analysis_results'][keyword]['OI'].remove(occurrence_id)
            else:
                oi_count += 1
                if occurrence_id not in isp_data['analysis_results'][keyword]['OI']:
                    isp_data['analysis_results'][keyword]['OI'].append(occurrence_id)
                if occurrence_id in isp_data['analysis_results'][keyword]['AA']:
                    isp_data['analysis_results'][keyword]['AA'].remove(occurrence_id)
                    
            # Update progress
            progress_bar.progress((i + 1) / len(sentences))
        
        st.info(f"Rule-based classification results for '{keyword}':\n"
                f"- Actionable Advice (AA): {aa_count}\n"
                f"- Other Information (OI): {oi_count}")
        
        return isp_data
    
    @staticmethod
    def batch_analyze(sentences: List[Dict], keyword: str, progress_bar=None) -> List[str]:
        """Analyze a batch of sentences and return classifications."""
        model = AIAnalyzer.load_model()
        
        if model is None:
            st.warning("Failed to load the AI model. Using rule-based classification instead.")
            # Use rule-based approach as fallback
            results = []
            total = len(sentences)
            for i, item in enumerate(sentences):
                sentence = item['sentence'].lower()
                is_actionable = False
                
                # Check for action words and vague terms
                action_markers = ["must ", "shall ", "required to ", "always ", "never ", 
                                 "do not ", "should ", "is prohibited", "is not permitted"]
                vague_terms = ["good time", "exercise caution", "be careful", "as appropriate",
                             "when necessary", "as needed", "reasonable", "proper"]
                
                if any(marker in sentence for marker in action_markers):
                    if not any(term in sentence for term in vague_terms):
                        is_actionable = True
                
                classification = "AA" if is_actionable else "OI"
                results.append(classification)
                
                if progress_bar is not None:
                    progress_bar.progress((i + 1) / total, 
                                         text=f"Simple classification {i+1}/{total}")
            return results
            
        results = []
        total = len(sentences)
        
        for i, item in enumerate(sentences):
            if progress_bar is not None:
                progress_bar.progress(i / total, text=f"Analyzing {i+1}/{total}")
                
            classification = AIAnalyzer.analyze_sentence(model, item, keyword)
            results.append(classification)
            
            if progress_bar is not None:
                progress_bar.progress((i + 1) / total, text=f"Completed {i+1}/{total}")
                
        return results
    
    @staticmethod
    def ai_analyze_keyword(isp_data: Dict, keyword: str) -> Dict:
        """Analyze sentences for a specific keyword and update isp_data."""
        if not LLAMA_CPP_AVAILABLE:
            st.error("The llama-cpp-python library is not installed. Using rule-based classification instead.")
            return AIAnalyzer.simple_analyze_keyword(isp_data, keyword)
            
        if 'analysis_results' not in isp_data:
            isp_data['analysis_results'] = {}
        
        # Get sentences with the keyword
        sentences = Analyzer.find_sentences_with_keyword(isp_data.get('text', ''), keyword)
        
        if not sentences:
            st.warning(f"No sentences found containing keyword '{keyword}'")
            if keyword not in isp_data['analysis_results']:
                isp_data['analysis_results'][keyword] = {'AA': [], 'OI': []}
            return isp_data
        
        st.info(f"Found {len(sentences)} sentences containing keyword '{keyword}'")
        
        # Setup progress bar
        progress_placeholder = st.empty()
        progress_bar = progress_placeholder.progress(0, text="Initializing...")
        
        # Classify sentences
        classifications = AIAnalyzer.batch_analyze(sentences, keyword, progress_bar)
        
        # Process results
        if keyword not in isp_data['analysis_results']:
            isp_data['analysis_results'][keyword] = {'AA': [], 'OI': []}
        
        aa_count = 0
        oi_count = 0
        
        for item, classification in zip(sentences, classifications):
            occurrence_id = f"{item['sentence']}::{item['start']}::{item['end']}"
            if classification == "AA":
                aa_count += 1
                if occurrence_id not in isp_data['analysis_results'][keyword]['AA']:
                    isp_data['analysis_results'][keyword]['AA'].append(occurrence_id)
                if occurrence_id in isp_data['analysis_results'][keyword]['OI']:
                    isp_data['analysis_results'][keyword]['OI'].remove(occurrence_id)
            else:
                oi_count += 1
                if occurrence_id not in isp_data['analysis_results'][keyword]['OI']:
                    isp_data['analysis_results'][keyword]['OI'].append(occurrence_id)
                if occurrence_id in isp_data['analysis_results'][keyword]['AA']:
                    isp_data['analysis_results'][keyword]['AA'].remove(occurrence_id)
        
        # Clear progress bar
        progress_placeholder.empty()
        
        # Show summary
        st.success(f"Analysis complete for '{keyword}':\n"
                  f"- Actionable Advice (AA): {aa_count}\n"
                  f"- Other Information (OI): {oi_count}")
        
        return isp_data
    
    @staticmethod
    def ai_analyze_all_keywords(isp_data: Dict, keywords: List[str]) -> Dict:
        """Analyze all keywords for an ISP."""
        if not keywords:
            return isp_data
        
        st.info(f"Starting analysis of {len(keywords)} keywords")
        
        total = len(keywords)
        progress_placeholder = st.empty()
        progress_text = st.empty()
        
        for i, keyword in enumerate(keywords):
            progress_text.text(f"Analyzing keyword {i+1}/{total}: '{keyword}'")
            progress_placeholder.progress(i / total)
            
            isp_data = AIAnalyzer.ai_analyze_keyword(isp_data, keyword)
            
        progress_placeholder.empty()
        progress_text.empty()
        
        return isp_data