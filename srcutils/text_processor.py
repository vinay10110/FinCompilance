import spacy
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from typing import List, Dict, Any, Optional
import re
from datetime import datetime

class TextProcessor:
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
            nltk.download('wordnet')
            nltk.download('averaged_perceptron_tagger')

        # Initialize NLP components
        self.nlp = spacy.load('en_core_web_sm')
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Regular expressions for different types of requirements
        self.requirement_patterns = {
            'mandatory': r'\b(must|shall|required|mandatory|necessary)\b',
            'recommended': r'\b(should|recommended|advisable)\b',
            'optional': r'\b(may|optional|can)\b',
            'deadline': r'\b(by|before|prior to|within|until)\s+([A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})',
        }

    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def extract_requirements(self, text: str) -> List[Dict[str, Any]]:
        """Extract requirements and their properties from text"""
        requirements = []
        doc = self.nlp(text)
        
        # Process each sentence
        for sent in doc.sents:
            requirement_type = self._identify_requirement_type(sent.text)
            if requirement_type:
                # Extract dates if present
                dates = self._extract_dates(sent.text)
                
                # Extract entities
                entities = self._extract_entities(sent)
                
                requirements.append({
                    'text': sent.text.strip(),
                    'type': requirement_type,
                    'dates': dates,
                    'entities': entities,
                    'keywords': self._extract_keywords(sent.text)
                })
        
        return requirements

    def analyze_changes(self, old_text: str, new_text: str) -> Dict[str, Any]:
        """Analyze changes between two versions of text"""
        # Convert texts to spaCy docs
        old_doc = self.nlp(old_text)
        new_doc = self.nlp(new_text)
        
        # Extract requirements from both versions
        old_reqs = self.extract_requirements(old_text)
        new_reqs = self.extract_requirements(new_text)
        
        # Compare requirements
        added = []
        modified = []
        removed = []
        
        for new_req in new_reqs:
            if not any(self._is_similar_requirement(new_req, old_req) 
                      for old_req in old_reqs):
                added.append(new_req)
            else:
                for old_req in old_reqs:
                    if self._is_similar_requirement(new_req, old_req) and \
                       new_req['text'] != old_req['text']:
                        modified.append({
                            'old': old_req,
                            'new': new_req
                        })
        
        for old_req in old_reqs:
            if not any(self._is_similar_requirement(old_req, new_req) 
                      for new_req in new_reqs):
                removed.append(old_req)
        
        return {
            'added': added,
            'modified': modified,
            'removed': removed,
            'summary': self._generate_change_summary(added, modified, removed)
        }

    def extract_key_metrics(self, text: str) -> Dict[str, Any]:
        """Extract key metrics and indicators from text"""
        doc = self.nlp(text)
        metrics = {
            'numerical_values': [],
            'percentages': [],
            'currencies': [],
            'dates': [],
            'organizations': [],
            'key_terms': []
        }
        
        # Extract numerical values and units
        for token in doc:
            if token.like_num:
                next_token = token.i + 1 < len(doc) and doc[token.i + 1]
                if next_token and next_token.text in ['%', 'percent', 'percentage']:
                    metrics['percentages'].append({
                        'value': float(token.text),
                        'context': self._get_context(doc, token)
                    })
                elif next_token and next_token.text in ['Rs.', '$', '€', '£']:
                    metrics['currencies'].append({
                        'value': float(token.text),
                        'currency': next_token.text,
                        'context': self._get_context(doc, token)
                    })
                else:
                    metrics['numerical_values'].append({
                        'value': float(token.text),
                        'context': self._get_context(doc, token)
                    })
        
        # Extract dates
        metrics['dates'] = self._extract_dates(text)
        
        # Extract organizations
        metrics['organizations'] = [
            ent.text for ent in doc.ents if ent.label_ == 'ORG'
        ]
        
        # Extract key terms
        metrics['key_terms'] = self._extract_keywords(text)
        
        return metrics

    def _identify_requirement_type(self, text: str) -> Optional[str]:
        """Identify the type of requirement based on key phrases"""
        for req_type, pattern in self.requirement_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return req_type
        return None

    def _extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """Extract dates and deadlines from text"""
        dates = []
        
        # Look for various date formats
        date_patterns = [
            r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
            r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{2}/\d{2}/\d{4})'
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    date_str = match.group(1)
                    # Convert to datetime object (implementation depends on format)
                    # For simplicity, storing as string here
                    dates.append({
                        'date': date_str,
                        'context': self._get_context(text, match)
                    })
                except ValueError:
                    continue
        
        return dates

    def _extract_entities(self, doc) -> Dict[str, List[str]]:
        """Extract named entities from text"""
        entities = {
            'organizations': [],
            'persons': [],
            'dates': [],
            'money': [],
            'percent': [],
            'law': []
        }
        
        for ent in doc.ents:
            if ent.label_ in entities:
                entities[ent.label_].append(ent.text)
        
        return entities

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Tokenize and lemmatize
        tokens = word_tokenize(text.lower())
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens 
                 if token not in self.stop_words and token.isalnum()]
        
        # Get word frequency
        freq_dist = nltk.FreqDist(tokens)
        
        # Return top keywords
        return [word for word, _ in freq_dist.most_common(5)]

    def _is_similar_requirement(self, req1: Dict[str, Any], 
                              req2: Dict[str, Any]) -> bool:
        """Check if two requirements are similar"""
        # Compare requirement texts using similarity score
        doc1 = self.nlp(req1['text'])
        doc2 = self.nlp(req2['text'])
        
        return doc1.similarity(doc2) > 0.8

    def _get_context(self, doc, token, window: int = 5) -> str:
        """Get surrounding context for a token"""
        start = max(0, token.i - window)
        end = min(len(doc), token.i + window + 1)
        return doc[start:end].text

    def _generate_change_summary(self, added: List[Dict], 
                               modified: List[Dict],
                               removed: List[Dict]) -> str:
        """Generate a human-readable summary of changes"""
        summary = []
        
        if added:
            summary.append(f"Added {len(added)} new requirements")
        if modified:
            summary.append(f"Modified {len(modified)} existing requirements")
        if removed:
            summary.append(f"Removed {len(removed)} requirements")
        
        return '. '.join(summary)