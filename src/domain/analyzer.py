import re
from typing import List, Dict, Set, Tuple, Optional

class SentenceExtractor:
    """Responsible for extracting sentences and finding keyword matches."""
    
    @staticmethod
    def extract_sentences(text: str) -> List[str]:
        """Split text into sentences."""
        sentences = re.split(r'\.(?:\s|\n|$)', text)
        return [s.strip() + '.' for s in sentences if s.strip()]
    
    @staticmethod
    def find_sentences_with_keyword(text: str, keyword: str) -> List[Dict]:
        """Find sentences that contain the specified keyword including context."""
        sentences = SentenceExtractor.extract_sentences(text)
        matching_sentences = []
        pattern = r'\b' + re.escape(keyword) + r'\b'
        
        for i, sentence in enumerate(sentences):
            matches = list(re.finditer(pattern, sentence, re.IGNORECASE))

            before_context = sentences[i-1] if i > 0 else ""
            after_context = sentences[i+1] if i < len(sentences)-1 else ""

            extended_before_context = []
            extended_after_context = []

            for j in range(i-5, i):
                if j >= 0 and j != i-1:
                    extended_before_context.append(sentences[j])
                
            for j in range(i+2, i+7):
                if j < len(sentences):
                    extended_after_context.append(sentences[j])

            if matches:
                for match in matches:
                    matching_sentences.append({
                        'sentence': sentence,
                        'start': match.start(),
                        'end': match.end(),
                        'match_text': match.group(),
                        'before_context': before_context,
                        'after_context': after_context,
                        'extended_before_context': extended_before_context,
                        'extended_after_context': extended_after_context
                    })
        return matching_sentences