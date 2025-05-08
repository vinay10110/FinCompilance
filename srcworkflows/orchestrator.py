from typing import Dict, List, Any, Annotated, TypedDict
from langchain.llms import Together
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolMessage
import json
from datetime import datetime
from ..srcagents.change_detection_agent import ChangeDetectionAgent
from ..srcagents.implementation_agent import ImplementationAgent
from ..srcagents.process_management_agent import ProcessManagementAgent
from ..srcagents.base_agent import AgentState

class WorkflowState(TypedDict):
    """The state of the workflow"""
    messages: List[Dict[str, Any]]
    change_analysis: Dict[str, Any]
    implementation_plan: Dict[str, Any]
    compliance_status: Dict[str, Any]
    current_phase: str
    next_steps: List[str]
    errors: List[str]

def create_workflow(
    llm: Together,
    config: Dict[str, Any]
) -> StateGraph:
    """Create the workflow graph for regulatory compliance automation"""
    
    # Initialize agents
    change_agent = ChangeDetectionAgent(llm=llm, verbose=True)
    implementation_agent = ImplementationAgent(llm=llm, verbose=True)
    process_agent = ProcessManagementAgent(llm=llm, verbose=True)
    
    # Create the workflow graph
    workflow = StateGraph(WorkflowState)
    
    # Define agent nodes
    def analyze_changes(state: WorkflowState) -> WorkflowState:
        """Analyze regulatory changes"""
        try:
            agent_state = AgentState(
                messages=state["messages"],
                current_task="Analyze new regulatory document for changes"
            )
            result = change_agent(agent_state)
            
            state["change_analysis"] = json.loads(result.messages[-1].content)
            state["next_steps"].append("create_implementation_plan")
            state["current_phase"] = "change_analysis_complete"
            
        except Exception as e:
            state["errors"].append(f"Error in change analysis: {str(e)}")
            state["next_steps"].append("error_handling")
        
        return state

    def create_implementation_plan(state: WorkflowState) -> WorkflowState:
        """Create implementation plan based on change analysis"""
        try:
            if not state.get("change_analysis"):
                state["errors"].append("No change analysis available")
                state["next_steps"].append("error_handling")
                return state
            
            agent_state = AgentState(
                messages=state["messages"],
                current_task=json.dumps({
                    "task": "create_implementation_plan",
                    "change_analysis": state["change_analysis"]
                })
            )
            result = implementation_agent(agent_state)
            
            state["implementation_plan"] = json.loads(result.messages[-1].content)
            state["next_steps"].append("verify_compliance")
            state["current_phase"] = "implementation_plan_complete"
            
        except Exception as e:
            state["errors"].append(f"Error in implementation planning: {str(e)}")
            state["next_steps"].append("error_handling")
        
        return state

    def verify_compliance(state: WorkflowState) -> WorkflowState:
        """Verify compliance of implementation plan"""
        try:
            if not state.get("implementation_plan"):
                state["errors"].append("No implementation plan available")
                state["next_steps"].append("error_handling")
                return state
            
            agent_state = AgentState(
                messages=state["messages"],
                current_task=json.dumps({
                    "task": "verify_compliance",
                    "implementation": state["implementation_plan"],
                    "requirements": state["change_analysis"]["requirements"]
                })
            )
            result = process_agent(agent_state)
            
            state["compliance_status"] = json.loads(result.messages[-1].content)
            state["current_phase"] = "compliance_verification_complete"
            
            # Determine next steps based on compliance status
            if state["compliance_status"]["verification_results"]["compliance_score"] < 100:
                state["next_steps"].append("revise_implementation")
            else:
                state["next_steps"].append("finalize_workflow")
            
        except Exception as e:
            state["errors"].append(f"Error in compliance verification: {str(e)}")
            state["next_steps"].append("error_handling")
        
        return state

    def revise_implementation(state: WorkflowState) -> WorkflowState:
        """Revise implementation plan based on compliance verification"""
        try:
            agent_state = AgentState(
                messages=state["messages"],
                current_task=json.dumps({
                    "task": "revise_implementation",
                    "implementation_plan": state["implementation_plan"],
                    "compliance_status": state["compliance_status"],
                    "change_analysis": state["change_analysis"]
                })
            )
            result = implementation_agent(agent_state)
            
            # Update implementation plan with revisions
            state["implementation_plan"] = json.loads(result.messages[-1].content)
            state["next_steps"].append("verify_compliance")
            state["current_phase"] = "implementation_revised"
            
        except Exception as e:
            state["errors"].append(f"Error in implementation revision: {str(e)}")
            state["next_steps"].append("error_handling")
        
        return state

    def handle_error(state: WorkflowState) -> WorkflowState:
        """Handle errors in the workflow"""
        if state["errors"]:
            error_msg = state["errors"][-1]
            state["messages"].append({
                "role": "system",
                "content": f"Error encountered: {error_msg}. Attempting recovery..."
            })
            
            # Determine recovery action based on current phase
            if state["current_phase"] == "change_analysis_complete":
                state["next_steps"] = ["create_implementation_plan"]
            elif state["current_phase"] == "implementation_plan_complete":
                state["next_steps"] = ["verify_compliance"]
            elif state["current_phase"] == "compliance_verification_complete":
                state["next_steps"] = ["revise_implementation"]
            else:
                state["next_steps"] = ["finalize_workflow"]
        
        return state

    def should_continue(state: WorkflowState) -> str:
        """Determine if workflow should continue or end"""
        if not state["next_steps"]:
            return "end"
        
        if len(state["errors"]) > config.get("max_retries", 3):
            return "end"
            
        next_step = state["next_steps"].pop(0)
        return next_step

    # Add nodes to workflow
    workflow.add_node("analyze_changes", analyze_changes)
    workflow.add_node("create_implementation_plan", create_implementation_plan)
    workflow.add_node("verify_compliance", verify_compliance)
    workflow.add_node("revise_implementation", revise_implementation)
    workflow.add_node("error_handling", handle_error)
    
    # Add edges
    workflow.add_conditional_edges(
        "analyze_changes",
        should_continue,
        {
            "create_implementation_plan": "create_implementation_plan",
            "error_handling": "error_handling",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "create_implementation_plan",
        should_continue,
        {
            "verify_compliance": "verify_compliance",
            "error_handling": "error_handling",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "verify_compliance",
        should_continue,
        {
            "revise_implementation": "revise_implementation",
            "error_handling": "error_handling",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "revise_implementation",
        should_continue,
        {
            "verify_compliance": "verify_compliance",
            "error_handling": "error_handling",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "error_handling",
        should_continue,
        {
            "analyze_changes": "analyze_changes",
            "create_implementation_plan": "create_implementation_plan",
            "verify_compliance": "verify_compliance",
            "revise_implementation": "revise_implementation",
            "end": END
        }
    )
    
    # Set entry point
    workflow.set_entry_point("analyze_changes")
    
    return workflow

class WorkflowOrchestrator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm = Together(
            model=config["model_name"],
            temperature=0.7,
            api_key=config["together_api_key"]
        )
        self.workflow = create_workflow(self.llm, config)
    
    async def run(self, initial_state: WorkflowState) -> WorkflowState:
        """Run the workflow with the given initial state"""
        app = self.workflow.compile()
        final_state = await app.ainvoke(initial_state)
        return final_state
    
    def create_initial_state(self) -> WorkflowState:
        """Create an initial workflow state"""
        return WorkflowState(
            messages=[],
            change_analysis={},
            implementation_plan={},
            compliance_status={},
            current_phase="initialized",
            next_steps=["analyze_changes"],
            errors=[]
        )