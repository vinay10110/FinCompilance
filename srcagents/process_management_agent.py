from typing import List, Dict, Any
from .base_agent import BaseAgent, AgentState
from langchain.tools import BaseTool
from langchain.llms import Together
import json
from datetime import datetime
from pathlib import Path

class CodeAnalysisTool(BaseTool):
    name = "code_analysis"
    description = "Analyze code and policy gaps against new requirements"
    
    def _run(self, 
             requirements: Dict[str, Any],
             current_code: Dict[str, str]) -> Dict[str, Any]:
        gaps = self._identify_gaps(requirements, current_code)
        changes = self._suggest_changes(gaps)
        impact = self._analyze_impact(changes)
        
        return {
            "gaps": gaps,
            "suggested_changes": changes,
            "impact_analysis": impact,
            "risk_assessment": self._assess_risks(changes)
        }
    
    def _identify_gaps(self, 
                      requirements: Dict[str, Any],
                      current_code: Dict[str, str]) -> List[Dict[str, Any]]:
        gaps = []
        for req_id, req in requirements.items():
            if req["type"] == "validation":
                gaps.extend(self._check_validation_rules(req, current_code))
            elif req["type"] == "reporting":
                gaps.extend(self._check_reporting_requirements(req, current_code))
            elif req["type"] == "process":
                gaps.extend(self._check_process_flows(req, current_code))
        
        return gaps
    
    def _suggest_changes(self, gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        changes = []
        for gap in gaps:
            changes.append({
                "file": gap["file"],
                "type": gap["type"],
                "description": gap["description"],
                "suggested_implementation": self._generate_implementation_suggestion(gap),
                "priority": self._calculate_priority(gap)
            })
        return changes
    
    def _analyze_impact(self, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        impact = {
            "high_risk_areas": [],
            "affected_systems": set(),
            "complexity_score": 0
        }
        
        for change in changes:
            if change["priority"] == "high":
                impact["high_risk_areas"].append(change)
            impact["affected_systems"].add(change["file"].split("/")[0])
            impact["complexity_score"] += self._calculate_complexity(change)
        
        impact["affected_systems"] = list(impact["affected_systems"])
        return impact
    
    def _assess_risks(self, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        risks = []
        for change in changes:
            risks.extend(self._identify_change_risks(change))
        return risks
    
    def _calculate_complexity(self, change: Dict[str, Any]) -> float:
        factors = {
            "high": 3.0,
            "medium": 2.0,
            "low": 1.0
        }
        return factors[change["priority"]] * len(change["suggested_implementation"])
    
    def _identify_change_risks(self, change: Dict[str, Any]) -> List[Dict[str, Any]]:
        risks = []
        risk_patterns = {
            "data_modification": {
                "keywords": ["update", "delete", "modify"],
                "risk_level": "high",
                "mitigation": "Implement transaction management and rollback mechanisms"
            },
            "security": {
                "keywords": ["authentication", "authorization", "credential"],
                "risk_level": "high",
                "mitigation": "Conduct security review and implement additional safeguards"
            },
            "performance": {
                "keywords": ["query", "loop", "batch"],
                "risk_level": "medium",
                "mitigation": "Optimize code and add performance monitoring"
            }
        }
        
        for risk_type, pattern in risk_patterns.items():
            if any(keyword in change["description"].lower() 
                  for keyword in pattern["keywords"]):
                risks.append({
                    "type": risk_type,
                    "level": pattern["risk_level"],
                    "description": f"Potential {risk_type} risk in {change['file']}",
                    "mitigation": pattern["mitigation"]
                })
        
        return risks

class ComplianceVerificationTool(BaseTool):
    name = "compliance_verification"
    description = "Verify implementation against regulatory requirements"
    
    def _run(self,
             implementation: Dict[str, Any],
             requirements: Dict[str, Any]) -> Dict[str, Any]:
        verification_results = self._verify_compliance(implementation, requirements)
        evidence = self._collect_evidence(verification_results)
        report = self._generate_report(verification_results, evidence)
        
        return {
            "verification_results": verification_results,
            "evidence": evidence,
            "compliance_report": report,
            "action_items": self._generate_action_items(verification_results)
        }
    
    def _verify_compliance(self,
                         implementation: Dict[str, Any],
                         requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        for req_id, req in requirements.items():
            verification = {
                "requirement_id": req_id,
                "requirement": req["description"],
                "status": "compliant",
                "findings": [],
                "evidence_refs": []
            }
            
            # Check implementation against requirements
            if req["type"] in implementation:
                impl = implementation[req["type"]]
                verification.update(self._check_requirement(req, impl))
            else:
                verification.update({
                    "status": "non_compliant",
                    "findings": ["Implementation not found for requirement"]
                })
            
            results.append(verification)
        
        return results
    
    def _collect_evidence(self, 
                         verification_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        evidence = {}
        for result in verification_results:
            if result["status"] == "compliant":
                evidence[result["requirement_id"]] = {
                    "type": "implementation_evidence",
                    "artifacts": self._gather_artifacts(result),
                    "timestamp": datetime.now().isoformat(),
                    "hash": self._generate_evidence_hash(result)
                }
        return evidence
    
    def _generate_report(self,
                        results: List[Dict[str, Any]],
                        evidence: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "summary": self._generate_summary(results),
            "detailed_findings": results,
            "evidence_inventory": evidence,
            "timestamp": datetime.now().isoformat(),
            "compliance_score": self._calculate_compliance_score(results)
        }
    
    def _generate_action_items(self, 
                             results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        actions = []
        for result in results:
            if result["status"] != "compliant":
                actions.append({
                    "requirement_id": result["requirement_id"],
                    "description": f"Address compliance gap: {result['findings'][0]}",
                    "priority": "high" if "critical" in result["requirement"].lower() 
                              else "medium",
                    "suggested_resolution": self._suggest_resolution(result)
                })
        return actions
    
    def _calculate_compliance_score(self, results: List[Dict[str, Any]]) -> float:
        total = len(results)
        compliant = sum(1 for r in results if r["status"] == "compliant")
        return (compliant / total) * 100 if total > 0 else 0

class ProcessManagementAgent(BaseAgent):
    def __init__(self, llm: Together, verbose: bool = False):
        tools = [
            CodeAnalysisTool(),
            ComplianceVerificationTool()
        ]
        
        system_prompt = """You are a specialized process management agent.
        Your role is to:
        1. Analyze code and policy gaps
        2. Suggest system changes and improvements
        3. Verify compliance with regulations
        4. Generate compliance reports and evidence
        5. Track implementation progress
        
        Use the provided tools to ensure proper implementation and compliance."""
        
        super().__init__(
            name="Process Management Agent",
            system_prompt=system_prompt,
            tools=tools,
            llm=llm,
            verbose=verbose
        )
    
    async def analyze_and_verify(self,
                               requirements: Dict[str, Any],
                               implementation: Dict[str, Any],
                               current_code: Dict[str, str]) -> Dict[str, Any]:
        """Analyze gaps and verify compliance"""
        
        # First analyze code and policy gaps
        analysis_state = AgentState(
            messages=[],
            current_task=json.dumps({
                "task": "analyze_code",
                "requirements": requirements,
                "current_code": current_code
            })
        )
        analysis_result = await self.execute(analysis_state)
        
        # Then verify compliance
        verification_state = AgentState(
            messages=[],
            current_task=json.dumps({
                "task": "verify_compliance",
                "implementation": implementation,
                "requirements": requirements
            })
        )
        verification_result = await self.execute(verification_state)
        
        return {
            "analysis": json.loads(analysis_result.messages[-1].content),
            "verification": json.loads(verification_result.messages[-1].content)
        }