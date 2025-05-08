from typing import Dict, List, Any
from .base_agent import BaseAgent, AgentState
from langchain.tools import BaseTool
from langchain.llms import Together
from ..srcutils.rbi_scraper import RBIWebScraper
import json
import asyncio
from datetime import datetime

class WebScraperTool(BaseTool):
    name = "web_scraper"
    description = "Scrape RBI website for new press releases and regulatory updates"
    
    def __init__(self):
        super().__init__()
        self.scraper = RBIWebScraper()
    
    def _run(self, task: str = "scrape") -> Dict[str, Any]:
        """Run the web scraper"""
        if task == "scrape":
            new_updates = self.scraper.scrape()
            return {
                "status": "success",
                "new_entries": len(new_updates),
                "updates": new_updates
            }
        elif task == "get_latest":
            latest = self.scraper.get_latest_updates()
            return {
                "status": "success",
                "entries": latest
            }
        return {
            "status": "error",
            "message": f"Unknown task: {task}"
        }

class ResearchAgent(BaseAgent):
    def __init__(self, llm: Together, verbose: bool = False):
        tools = [
            WebScraperTool(),
            # Add search tool here later
        ]
        
        system_prompt = """You are a specialized research agent for regulatory compliance.
        Your role is to:
        1. Monitor RBI website for new press releases and regulatory updates
        2. Extract and process key information from updates
        3. Identify important regulatory changes
        4. Prepare summaries of new regulations
        
        Use the provided tools to gather and process regulatory information."""
        
        super().__init__(
            name="Research Agent",
            system_prompt=system_prompt,
            tools=tools,
            llm=llm,
            verbose=verbose
        )
    
    async def check_for_updates(self) -> Dict[str, Any]:
        """Check for new regulatory updates"""
        try:
            # Create state for web scraping task
            state = AgentState(
                messages=[],
                current_task=json.dumps({
                    "task": "check_updates",
                    "timestamp": datetime.now().isoformat()
                })
            )
            
            # Execute web scraping
            result = await self.execute(state)
            return json.loads(result.messages[-1].content)
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_latest_updates(self) -> Dict[str, Any]:
        """Get latest stored updates"""
        try:
            # Create state for fetching latest updates
            state = AgentState(
                messages=[],
                current_task=json.dumps({
                    "task": "get_latest",
                    "timestamp": datetime.now().isoformat()
                })
            )
            
            # Execute fetching latest updates
            result = await self.execute(state)
            return json.loads(result.messages[-1].content)
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }