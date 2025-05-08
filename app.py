import asyncio
from typing import Dict, Any
import os
from dotenv import load_dotenv
from srcconfig.config import settings
from srcworkflows.orchestrator import WorkflowOrchestrator
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComplianceAutomationSystem:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize configuration
        self.config = {
            "together_api_key": os.getenv("TOGETHER_API_KEY"),
            "model_name": settings.MODEL_NAME,
            "max_retries": 3,
            "rbi_base_url": settings.RBI_BASE_URL,
            "rbi_updates_url": settings.RBI_UPDATES_URL
        }
        
        # Initialize workflow orchestrator
        self.orchestrator = WorkflowOrchestrator(self.config)
        
    async def process_regulatory_update(self, document_path: str) -> Dict[str, Any]:
        """Process a new regulatory update document"""
        try:
            logger.info(f"Processing regulatory update from: {document_path}")
            
            # Create initial workflow state
            initial_state = self.orchestrator.create_initial_state()
            
            # Add document information to messages
            initial_state["messages"].append({
                "role": "system",
                "content": f"Processing regulatory document: {document_path}"
            })
            
            # Run the workflow
            final_state = await self.orchestrator.run(initial_state)
            
            # Save results
            self._save_results(final_state)
            
            return {
                "status": "success",
                "change_analysis": final_state["change_analysis"],
                "implementation_plan": final_state["implementation_plan"],
                "compliance_status": final_state["compliance_status"]
            }
            
        except Exception as e:
            logger.error(f"Error processing regulatory update: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _save_results(self, state: Dict[str, Any]):
        """Save workflow results to disk"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = "results"
        
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        
        # Save complete state
        with open(f"{results_dir}/workflow_state_{timestamp}.json", "w") as f:
            json.dump(state, f, indent=2)
        
        # Save implementation plan separately
        if state.get("implementation_plan"):
            with open(f"{results_dir}/implementation_plan_{timestamp}.json", "w") as f:
                json.dump(state["implementation_plan"], f, indent=2)
        
        # Save compliance report
        if state.get("compliance_status"):
            with open(f"{results_dir}/compliance_report_{timestamp}.json", "w") as f:
                json.dump(state["compliance_status"], f, indent=2)

async def main():
    # Initialize the system
    system = ComplianceAutomationSystem()
    
    # Example usage
    result = await system.process_regulatory_update("rbi_updates/RBIs Core Purpose Values and Vision_20250508.pdf")
    
    if result["status"] == "success":
        print("\nRegulatory Update Processing Complete")
        print("\nChange Analysis Summary:")
        print(json.dumps(result["change_analysis"], indent=2))
        
        print("\nImplementation Plan Summary:")
        print(json.dumps(result["implementation_plan"], indent=2))
        
        print("\nCompliance Status:")
        print(json.dumps(result["compliance_status"], indent=2))
    else:
        print(f"\nError: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())