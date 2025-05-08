from typing import List, Dict, Any
from .base_agent import BaseAgent, AgentState
from langchain.tools import BaseTool
from langchain.llms import Together
import networkx as nx
from datetime import datetime, timedelta
import json

class RoadmapGeneratorTool(BaseTool):
    name = "roadmap_generator"
    description = "Generate implementation roadmap with tasks and dependencies"
    
    def _run(self, 
             change_analysis: Dict[str, Any],
             available_resources: Dict[str, Any]) -> Dict[str, Any]:
        # Create task graph
        task_graph = self._create_task_graph(change_analysis)
        
        # Generate timeline
        timeline = self._generate_timeline(task_graph, available_resources)
        
        # Assign resources
        assignments = self._assign_resources(timeline, available_resources)
        
        return {
            "timeline": timeline,
            "resource_assignments": assignments,
            "critical_path": self._identify_critical_path(task_graph),
            "milestones": self._generate_milestones(timeline)
        }
    
    def _create_task_graph(self, change_analysis: Dict[str, Any]) -> nx.DiGraph:
        G = nx.DiGraph()
        
        # Define standard task templates based on affected areas
        task_templates = {
            "technical": [
                ("system_analysis", "design_changes", 5),
                ("design_changes", "implementation", 10),
                ("implementation", "testing", 5),
                ("testing", "deployment", 3)
            ],
            "operational": [
                ("process_review", "process_update", 5),
                ("process_update", "staff_training", 7),
                ("staff_training", "go_live", 3)
            ],
            "compliance": [
                ("compliance_review", "documentation", 5),
                ("documentation", "approval", 3),
                ("approval", "implementation", 2)
            ]
        }
        
        # Add tasks based on affected areas
        for area in change_analysis["affected_areas"]:
            if area in task_templates:
                for source, target, duration in task_templates[area]:
                    G.add_edge(f"{area}_{source}", 
                              f"{area}_{target}", 
                              duration=duration)
        
        return G
    
    def _generate_timeline(self, 
                          task_graph: nx.DiGraph,
                          resources: Dict[str, Any]) -> List[Dict[str, Any]]:
        timeline = []
        start_date = datetime.now()
        
        # Calculate early start and late start for each task
        early_start = {}
        for task in nx.topological_sort(task_graph):
            predecessors = list(task_graph.predecessors(task))
            if not predecessors:
                early_start[task] = 0
            else:
                early_start[task] = max(early_start[p] + task_graph[p][task]["duration"]
                                      for p in predecessors)
            
            timeline.append({
                "task": task,
                "start_date": start_date + timedelta(days=early_start[task]),
                "duration": task_graph.out_edges(task)[0]["duration"]
                if task_graph.out_edges(task) else 0,
                "dependencies": predecessors
            })
        
        return timeline
    
    def _assign_resources(self,
                         timeline: List[Dict[str, Any]],
                         resources: Dict[str, Any]) -> Dict[str, List[str]]:
        assignments = {}
        for task in timeline:
            task_type = task["task"].split("_")[0]
            if task_type in resources:
                assignments[task["task"]] = resources[task_type][:2]  # Assign up to 2 resources
        return assignments
    
    def _identify_critical_path(self, task_graph: nx.DiGraph) -> List[str]:
        # Find critical path using longest path in DAG
        critical_path = nx.dag_longest_path(task_graph, weight="duration")
        return critical_path
    
    def _generate_milestones(self, timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        milestones = []
        for task in timeline:
            if any(key in task["task"].lower() 
                  for key in ["deployment", "go_live", "approval"]):
                milestones.append({
                    "name": f"Complete {task['task']}",
                    "date": task["start_date"] + timedelta(days=task["duration"]),
                    "description": f"Major milestone: {task['task']}"
                })
        return milestones

class ResourceAllocationTool(BaseTool):
    name = "resource_allocation"
    description = "Calculate and allocate resources for implementation tasks"
    
    def _run(self, 
             timeline: List[Dict[str, Any]],
             available_resources: Dict[str, Any]) -> Dict[str, Any]:
        # Calculate resource requirements
        requirements = self._calculate_requirements(timeline)
        
        # Optimize resource allocation
        allocation = self._optimize_allocation(requirements, available_resources)
        
        # Generate resource schedule
        schedule = self._generate_schedule(allocation, timeline)
        
        return {
            "requirements": requirements,
            "allocation": allocation,
            "schedule": schedule,
            "resource_utilization": self._calculate_utilization(schedule)
        }
    
    def _calculate_requirements(self, timeline: List[Dict[str, Any]]) -> Dict[str, int]:
        requirements = {}
        for task in timeline:
            task_type = task["task"].split("_")[0]
            requirements[task_type] = requirements.get(task_type, 0) + 1
        return requirements
    
    def _optimize_allocation(self,
                           requirements: Dict[str, int],
                           resources: Dict[str, Any]) -> Dict[str, List[str]]:
        allocation = {}
        for task_type, count in requirements.items():
            if task_type in resources:
                available = resources[task_type]
                # Allocate resources based on task requirements
                needed_resources = min(count * 2, len(available))  # Up to 2 resources per task
                allocation[task_type] = available[:needed_resources]
        return allocation
    
    def _generate_schedule(self,
                          allocation: Dict[str, List[str]],
                          timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        schedule = []
        resource_assignments = {}
        
        for task in timeline:
            task_type = task["task"].split("_")[0]
            if task_type in allocation:
                available_resources = [
                    r for r in allocation[task_type]
                    if r not in resource_assignments or
                    resource_assignments[r] <= task["start_date"]
                ]
                
                if available_resources:
                    resource = available_resources[0]
                    end_date = task["start_date"] + timedelta(days=task["duration"])
                    resource_assignments[resource] = end_date
                    
                    schedule.append({
                        "task": task["task"],
                        "resource": resource,
                        "start_date": task["start_date"],
                        "end_date": end_date
                    })
        
        return schedule
    
    def _calculate_utilization(self, 
                             schedule: List[Dict[str, Any]]) -> Dict[str, float]:
        utilization = {}
        total_duration = (max(task["end_date"] for task in schedule) -
                        min(task["start_date"] for task in schedule)).days
        
        for task in schedule:
            resource = task["resource"]
            duration = (task["end_date"] - task["start_date"]).days
            utilization[resource] = utilization.get(resource, 0) + duration
        
        # Convert to percentage
        for resource in utilization:
            utilization[resource] = (utilization[resource] / total_duration) * 100
            
        return utilization

class ImplementationAgent(BaseAgent):
    def __init__(self, llm: Together, verbose: bool = False):
        tools = [
            RoadmapGeneratorTool(),
            ResourceAllocationTool()
        ]
        
        system_prompt = """You are a specialized implementation planning agent.
        Your role is to:
        1. Generate detailed implementation roadmaps
        2. Create task dependencies and timelines
        3. Allocate resources efficiently
        4. Identify critical paths and milestones
        5. Monitor resource utilization and suggest optimizations
        
        Use the provided tools to create comprehensive implementation plans."""
        
        super().__init__(
            name="Implementation Planning Agent",
            system_prompt=system_prompt,
            tools=tools,
            llm=llm,
            verbose=verbose
        )
        
    async def create_implementation_plan(self, 
                                      change_analysis: Dict[str, Any],
                                      available_resources: Dict[str, Any]) -> Dict[str, Any]:
        """Create a complete implementation plan based on change analysis"""
        state = AgentState(
            messages=[],
            current_task=json.dumps({
                "task": "create_implementation_plan",
                "change_analysis": change_analysis,
                "available_resources": available_resources
            })
        )
        
        updated_state = await self.execute(state)
        return json.loads(updated_state.messages[-1].content)