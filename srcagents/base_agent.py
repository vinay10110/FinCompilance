from typing import Dict, List, Any
from pydantic import BaseModel
from langchain.schema import BaseMessage
from langgraph.prebuilt import ToolMessage
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain.schema.messages import HumanMessage, SystemMessage
from langchain.prompts import MessagesPlaceholder
from langchain.llms import Together

class AgentState(BaseModel):
    """State tracked for each agent in the system"""
    messages: List[BaseMessage]
    current_task: str = ""
    intermediate_steps: List[tuple] = []
    
class BaseAgent:
    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: List[BaseTool],
        llm: Together,
        verbose: bool = False
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools
        self.llm = llm
        self.verbose = verbose
        
        # Initialize the agent
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=tools,
            verbose=verbose,
            handle_parsing_errors=True
        )
    
    def _create_agent(self) -> OpenAIFunctionsAgent:
        prompt = OpenAIFunctionsAgent.create_prompt(
            system_message=self.system_prompt,
            extra_prompt_messages=[
                MessagesPlaceholder(variable_name="chat_history"),
                MessagesPlaceholder(variable_name="intermediate_steps")
            ]
        )
        
        return OpenAIFunctionsAgent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
    
    async def execute(self, state: AgentState) -> AgentState:
        """Execute the agent on the current state"""
        result = await self.agent_executor.ainvoke(
            {
                "input": state.current_task,
                "chat_history": state.messages,
                "intermediate_steps": state.intermediate_steps
            }
        )
        
        # Update state with results
        state.messages.append(HumanMessage(content=state.current_task))
        if isinstance(result["output"], str):
            state.messages.append(ToolMessage(content=result["output"]))
        
        return state
    
    def __call__(self, state: AgentState) -> AgentState:
        """Synchronous execution wrapper"""
        import asyncio
        return asyncio.run(self.execute(state))