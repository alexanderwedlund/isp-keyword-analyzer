from typing import Dict, List, Any, Optional, Callable
import streamlit as st
from src.domain.ai.model import ModelManager

class SentenceClassifier:
    """Classifies sentences using AI assistance."""
    
    def __init__(self):
        self.model = None
    
    def ensure_model_loaded(self):
        """Ensure the model is loaded."""

        if not st.session_state.get("ai_available", False):
            return False

        if self.model is None:
            self.model = ModelManager.load_model()
        return self.model is not None
    
    def get_classification_with_rationale(self, sentence_data: Dict[str, Any], keyword: str) -> Dict[str, str]:
        """Get classification with rationale for a sentence in a single model call."""
        if not st.session_state.get("ai_available", False) or not self.ensure_model_loaded():
            return self._rule_based_classification(sentence_data, keyword)
        
        sentence = sentence_data['sentence']
        before_context = sentence_data.get('before_context', '')
        after_context = sentence_data.get('after_context', '')
        extended_before = "\n".join(sentence_data.get('extended_before_context', []))
        extended_after = "\n".join(sentence_data.get('extended_after_context', []))
        
        start_pos = sentence_data['start']
        end_pos = sentence_data['end']
        match_text = sentence_data['match_text']
        
        highlighted_sentence = (
            sentence[:start_pos] + 
            "[" + match_text + "]" + 
            sentence[end_pos:]
        )
        
        prompt = f"""Classification task for Information Security Policy (ISP) analysis:

Please classify the following sentence as either:
- 'AA' (Actionable Advice): Sentences that contain sufficient information to act upon without any ambiguity.
- 'OI' (Other Information): Sentences that are ambiguous, too abstract, or lack specific instructions.

IMPORTANT: Focus specifically on classifying the sentence containing the HIGHLIGHTED KEYWORD in [square brackets]. This is the target sentence you need to classify.

Thoroughly analyze the FULL CONTEXT before making your classification. Context often provides critical clues about whether a statement should be classified as AA or OI.

Evaluation Criteria:
1. Actionability: Can an employee take concrete, specific actions based solely on this information? AA requires clear direction on what to do or not do.
2. Clarity: Is the instruction clear enough to be followed without significant interpretation? (Note: Not every detail needs to be spelled out as long as the required action is clear)
3. Contextual relevance: Does the surrounding context modify how the statement should be interpreted?

Guidelines:
- Actionable Advice (AA): Specific, unambiguous instructions that employees can directly implement without interpretation. 
Examples: "Passwords must not be given over the phone", "Read e-mail that does not need to be saved should be deleted"

- Other Information (OI): This includes:
1. Ambiguous instructions (e.g., "orders must be submitted to IT in good time" - "good time" is subjective)
2. Vague guidance (e.g., "all staff must exercise caution when using e-mail" - doesn't specify how)
3. Abstract statements that indicate general direction but aren't directly actionable
4. Strategic statements despite containing relevant keywords

IMPORTANT DISTINCTION EXAMPLE:
- "Do [not] leave sensitive documents visible on your desk when leaving it unattended" should be classified as AA.
  Why? Even though it doesn't specify exactly what constitutes "sensitive documents" or what alternative action to take, it provides a clear, actionable instruction (don't leave documents visible). Employees can immediately understand and follow this directive.

- "Orders must be submitted to IT in good time" should be classified as OI.
  Why? The phrase "good time" is too vague to be actionable. Employees cannot determine when exactly to submit orders, making the instruction unimplementable without further clarification.

The key distinction is whether an employee can take a specific action based on the instruction, even if some details are left to reasonable interpretation.

Keyword being analyzed: {keyword}

FULL CONTEXT ANALYSIS:
Previous sentences: 
{extended_before}

Immediate previous context: 
{before_context}

TARGET SENTENCE TO CLASSIFY: "{highlighted_sentence}"

Immediate following context: 
{after_context}

Following sentences:
{extended_after}

YOUR RESPONSE FORMAT:
First line: Classification (AA or OI)
Following lines: 3-5 sentences explaining your classification in {st.session_state.language} language.

Example response (english language example - your response is in {st.session_state.language}):
AA
This sentence provides clear, specific instructions that can be directly implemented. The keyword [Must] appears in a context that requires definite action. The statement is unambiguous about what employees should do.
"""
        
        try:
            response = self.model.create_chat_completion(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.1,
            )
            
            response_text = response["choices"][0]["message"]["content"].strip()
            
            lines = response_text.split('\n', 1)
            if len(lines) >= 2:
                classification = lines[0].strip().upper()
                rationale = lines[1].strip()
                
                if "AA" in classification:
                    classification = "AA"
                else:
                    classification = "OI"
                
                return {
                    "classification": classification,
                    "rationale": rationale
                }
            else:
                if "AA" in response_text.upper():
                    return {"classification": "AA", "rationale": "Based on AI analysis."}
                else:
                    return {"classification": "OI", "rationale": "Based on AI analysis."}
                
        except Exception as e:
            st.error(f"Error in model inference: {e}")
            return self._rule_based_classification(sentence_data, keyword)
    
    def classify_sentence(self, sentence_data: Dict[str, Any], keyword: str) -> str:
        """Classify a sentence as 'AA' or 'OI'."""
        result = self.get_classification_with_rationale(sentence_data, keyword)
        return result["classification"]
    
    # Fallback
    def _rule_based_classification(self, sentence_data: Dict[str, Any], keyword: str) -> Dict[str, str]:
        """Rule-based fallback classification method."""
        sentence = sentence_data['sentence'].lower()
        
        start_pos = sentence_data['start']
        end_pos = sentence_data['end']
        match_text = sentence_data['match_text']
        
        highlighted_sentence = (
            sentence[:start_pos] + 
            "[" + match_text + "]" + 
            sentence[end_pos:]
        )
        
        action_markers = ["must ", "shall ", "required to ", "always ", "never ", 
                        "do not ", "should ", "is prohibited", "is not permitted"]
        
        vague_terms = ["good time", "exercise caution", "be careful", "as appropriate",
                    "when necessary", "as needed", "reasonable", "proper"]
        
        is_actionable = False
        if any(marker in sentence for marker in action_markers):
            if not any(term in sentence for term in vague_terms):
                is_actionable = True
        
        classification = "AA" if is_actionable else "OI"
        
        if classification == "AA":
            action_words = [marker for marker in action_markers if marker in sentence]
            rationale = f"This sentence contains clear action words ({', '.join(action_words)}) without ambiguous terms, making it specific enough to be actionable. The instruction is clear and provides concrete guidance that can be directly implemented. The highlighted keyword [{match_text}] appears in a context that provides definite direction."
        else:
            if any(term in sentence for term in vague_terms):
                vague_found = [term for term in vague_terms if term in sentence]
                rationale = f"Although the sentence contains the highlighted keyword [{match_text}], it uses vague terminology ({', '.join(vague_found)}) that makes the guidance ambiguous. This lack of specificity means it cannot be directly acted upon without additional interpretation."
            elif not any(marker in sentence for marker in action_markers):
                rationale = f"This sentence lacks clear action words that would make it actionable. The highlighted keyword [{match_text}] appears in a context that is more informational rather than providing specific guidance. Without explicit direction on what to do, it should be classified as Other Information."
            else:
                rationale = f"While the sentence contains the highlighted keyword [{match_text}], it does not provide clear, specific instructions that can be directly implemented. The statement is more informational than actionable."
        
        return {
            "classification": classification,
            "rationale": rationale
        }


class BatchClassifier:
    """Handles batch classification of sentences."""
    
    def __init__(self):
        self.classifier = SentenceClassifier()
    
    def classify_sentences(self, sentences: List[Dict], keyword: str, 
                          progress_callback: Optional[Callable] = None) -> List[str]:
        """Classify a batch of sentences."""
        results = []
        total = len(sentences)
        
        for i, item in enumerate(sentences):
            if progress_callback:
                progress_callback(i / total, f"Analyzing {i+1}/{total}")
                
            classification = self.classifier.classify_sentence(item, keyword)
            results.append(classification)
            
            if progress_callback:
                progress_callback((i + 1) / total, f"Completed {i+1}/{total}")
                
        return results
    
    # Fallback
    def simple_analyze_keyword(self, isp_data: Dict, keyword: str) -> Dict:
        """Simple rule-based classification as fallback when AI is not available."""
        from src.domain.analyzer import SentenceExtractor
        
        if 'analysis_results' not in isp_data:
            isp_data['analysis_results'] = {}
        
        sentences = SentenceExtractor.find_sentences_with_keyword(isp_data.get('text', ''), keyword)
        
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
            
            action_markers = ["must ", "shall ", "required to ", "always ", "never ", 
                             "do not ", "should ", "is prohibited", "is not permitted"]
            
            vague_terms = ["good time", "exercise caution", "be careful", "as appropriate",
                         "when necessary", "as needed", "reasonable", "proper"]
            
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
                    
            progress_bar.progress((i + 1) / len(sentences))
        
        st.info(f"Rule-based classification results for '{keyword}':\n"
                f"- Actionable Advice (AA): {aa_count}\n"
                f"- Other Information (OI): {oi_count}")
        
        return isp_data