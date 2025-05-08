from typing import List, Dict, Any
from .base_agent import BaseAgent, AgentState
from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field
from langchain.llms import Together
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
import numpy as np
from difflib import SequenceMatcher

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')

class ChangeClassificationTool(BaseTool):
    name = "change_classification"
    description = "Classify regulatory changes as minor, moderate, or major"
    
    def _run(self, text: str) -> Dict[str, Any]:
        # Implement sophisticated change classification logic
        impact_score = self._calculate_impact_score(text)
        category = self._categorize_change(impact_score)
        affected_areas = self._identify_affected_areas(text)
        
        return {
            "category": category,
            "impact_score": impact_score,
            "affected_areas": affected_areas,
            "estimated_timeline": self._suggest_timeline(category)
        }
    
    def _calculate_impact_score(self, text: str) -> float:
        # Implement impact scoring based on key indicators
        impact_indicators = {
            "mandatory": 0.8,
            "immediate effect": 0.9,
            "compliance": 0.7,
            "penalty": 0.8,
            "revision": 0.5,
            "amendment": 0.6,
            "new requirement": 0.7,
        }
        
        score = 0
        text_lower = text.lower()
        for indicator, weight in impact_indicators.items():
            if indicator in text_lower:
                score += weight
                
        return min(score / len(impact_indicators), 1.0)
    
    def _categorize_change(self, impact_score: float) -> str:
        if impact_score >= 0.7:
            return "major"
        elif impact_score >= 0.4:
            return "moderate"
        return "minor"
    
    def _identify_affected_areas(self, text: str) -> List[str]:
        # Implement affected areas identification
        areas = {
            "technical": ["system", "technology", "software", "infrastructure"],
            "operational": ["process", "procedure", "operation"],
            "financial": ["capital", "financial", "monetary", "funding"],
            "reporting": ["report", "disclosure", "filing"],
            "compliance": ["compliance", "regulatory", "governance"]
        }
        
        affected = []
        text_lower = text.lower()
        for area, keywords in areas.items():
            if any(keyword in text_lower for keyword in keywords):
                affected.append(area)
                
        return affected
    
    def _suggest_timeline(self, category: str) -> Dict[str, Any]:
        timelines = {
            "major": {"min_days": 90, "recommended_days": 120},
            "moderate": {"min_days": 45, "recommended_days": 60},
            "minor": {"min_days": 15, "recommended_days": 30}
        }
        return timelines[category]

class DifferentialAnalysisTool(BaseTool):
    name = "differential_analysis"
    description = "Analyze differences between new and previous regulations"
    
    def _run(self, old_text: str, new_text: str) -> Dict[str, Any]:
        # Implement differential analysis
        changes = self._detect_changes(old_text, new_text)
        significance = self._analyze_significance(changes)
        
        return {
            "changes": changes,
            "significance": significance,
            "summary": self._generate_summary(changes)
        }
    
    def _detect_changes(self, old_text: str, new_text: str) -> List[Dict[str, Any]]:
        old_sentences = sent_tokenize(old_text)
        new_sentences = sent_tokenize(new_text)
        changes = []
        
        for i, new_sent in enumerate(new_sentences):
            max_ratio = 0
            most_similar_idx = -1
            
            for j, old_sent in enumerate(old_sentences):
                ratio = SequenceMatcher(None, new_sent, old_sent).ratio()
                if ratio > max_ratio:
                    max_ratio = ratio
                    most_similar_idx = j
            
            if max_ratio < 0.8:  # New or significantly changed
                changes.append({
                    "type": "addition" if max_ratio < 0.3 else "modification",
                    "content": new_sent,
                    "similarity": max_ratio
                })
                
        return changes
    
    def _analyze_significance(self, changes: List[Dict[str, Any]]) -> float:
        # Calculate significance score based on changes
        weights = {"addition": 1.0, "modification": 0.7}
        total_score = sum(weights[change["type"]] * (1 - change["similarity"]) 
                         for change in changes)
        return min(total_score / len(changes) if changes else 0, 1.0)
    
    def _generate_summary(self, changes: List[Dict[str, Any]]) -> str:
        summary = []
        for change in changes:
            prefix = "Added: " if change["type"] == "addition" else "Modified: "
            summary.append(f"{prefix}{change['content'][:100]}...")
        return "\n".join(summary)

class ChangeDetectionAgent(BaseAgent):
    def __init__(self, llm: Together, verbose: bool = False):
        tools = [
            ChangeClassificationTool(),
            DifferentialAnalysisTool()
        ]
        
        system_prompt = """You are a specialized agent for detecting and classifying regulatory changes.
        Your role is to:
        1. Analyze new regulatory documents
        2. Classify the importance and impact of changes
        3. Identify affected areas and systems
        4. Suggest implementation timelines
        5. Generate detailed change reports
        
        Use the provided tools to perform your analysis and make recommendations."""
        
        super().__init__(
            name="Change Detection Agent",
            system_prompt=system_prompt,
            tools=tools,
            llm=llm,
            verbose=verbose
        )