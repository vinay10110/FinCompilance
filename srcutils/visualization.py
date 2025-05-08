import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
import json

class ComplianceVisualizer:
    def __init__(self):
        # Set default color schemes
        self.status_colors = {
            'compliant': '#2ecc71',
            'non_compliant': '#e74c3c',
            'partial': '#f1c40f',
            'in_progress': '#3498db',
            'not_started': '#95a5a6'
        }
    
    def create_compliance_dashboard(self,
                                 data: Dict[str, Any],
                                 output_path: str) -> str:
        """Create a comprehensive compliance dashboard"""
        # Create subplots layout
        fig = go.Figure()
        
        # Add compliance score gauge
        self._add_compliance_gauge(fig, data['compliance_score'])
        
        # Add requirements status breakdown
        self._add_requirements_breakdown(fig, data['requirements'])
        
        # Add timeline if available
        if 'timeline' in data:
            self._add_timeline(fig, data['timeline'])
        
        # Update layout
        fig.update_layout(
            title='Compliance Analysis Dashboard',
            showlegend=True,
            height=800,
            width=1200,
            grid={'rows': 2, 'columns': 2, 'pattern': 'independent'}
        )
        
        # Save dashboard
        fig.write_html(output_path)
        return output_path
    
    def create_requirements_network(self,
                                 requirements: List[Dict[str, Any]],
                                 dependencies: List[Dict[str, Any]],
                                 output_path: str) -> str:
        """Create an interactive network visualization of requirements"""
        # Create network graph
        G = nx.DiGraph()
        
        # Add nodes (requirements)
        for req in requirements:
            G.add_node(
                req['id'],
                status=req['status'],
                priority=req.get('priority', 'medium'),
                description=req['text']
            )
        
        # Add edges (dependencies)
        for dep in dependencies:
            G.add_edge(
                dep['source']['id'],
                dep['target']['id'],
                type=dep['type']
            )
        
        # Calculate layout
        pos = nx.spring_layout(G)
        
        # Create Plotly figure
        edge_trace = self._create_edge_trace(G, pos)
        node_trace = self._create_node_trace(G, pos)
        
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title='Requirements Dependency Network',
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
        )
        
        # Save visualization
        fig.write_html(output_path)
        return output_path
    
    def create_change_timeline(self,
                             changes: List[Dict[str, Any]],
                             output_path: str) -> str:
        """Create a timeline visualization of regulatory changes"""
        # Convert changes to DataFrame
        df = pd.DataFrame(changes)
        
        # Create timeline
        fig = px.timeline(
            df,
            x_start='effective_date',
            x_end='implementation_deadline',
            y='requirement',
            color='status',
            title='Regulatory Changes Timeline',
            color_discrete_map=self.status_colors
        )
        
        # Update layout
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Requirement',
            height=600
        )
        
        # Save visualization
        fig.write_html(output_path)
        return output_path
    
    def create_implementation_plan(self,
                                 tasks: List[Dict[str, Any]],
                                 output_path: str) -> str:
        """Create a Gantt chart for implementation planning"""
        # Convert tasks to DataFrame
        df = pd.DataFrame(tasks)
        
        # Create Gantt chart
        fig = px.timeline(
            df,
            x_start='start_date',
            x_end='end_date',
            y='task',
            color='status',
            title='Implementation Plan',
            color_discrete_map=self.status_colors
        )
        
        # Add resource allocation indicators
        if 'resources' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['end_date'],
                    y=df['task'],
                    mode='markers',
                    marker=dict(
                        symbol='diamond',
                        size=10,
                        color=df['resources'].map(len),
                        colorscale='Viridis',
                        showscale=True
                    ),
                    name='Resource Count'
                )
            )
        
        # Update layout
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Task',
            height=600,
            showlegend=True
        )
        
        # Save visualization
        fig.write_html(output_path)
        return output_path
    
    def create_risk_heatmap(self,
                           risks: List[Dict[str, Any]],
                           output_path: str) -> str:
        """Create a risk assessment heatmap"""
        # Convert risks to matrix format
        risk_matrix = self._prepare_risk_matrix(risks)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=risk_matrix['values'],
            x=risk_matrix['likelihood_levels'],
            y=risk_matrix['impact_levels'],
            colorscale='RdYlGn_r',
            showscale=True
        ))
        
        # Add risk points
        for risk in risks:
            fig.add_trace(go.Scatter(
                x=[risk['likelihood']],
                y=[risk['impact']],
                mode='markers+text',
                name=risk['name'],
                text=[risk['name']],
                textposition="top center",
                marker=dict(
                    size=10,
                    symbol='circle',
                    color='black'
                )
            ))
        
        # Update layout
        fig.update_layout(
            title='Risk Assessment Heatmap',
            xaxis_title='Likelihood',
            yaxis_title='Impact',
            height=600,
            width=800
        )
        
        # Save visualization
        fig.write_html(output_path)
        return output_path
    
    def _add_compliance_gauge(self,
                            fig: go.Figure,
                            score: float) -> None:
        """Add compliance score gauge to dashboard"""
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=score,
            domain={'x': [0, 0.5], 'y': [0.5, 1]},
            title={'text': "Compliance Score"},
            gauge={
                'axis': {'range': [0, 100]},
                'steps': [
                    {'range': [0, 60], 'color': "red"},
                    {'range': [60, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            }
        ))
    
    def _add_requirements_breakdown(self,
                                  fig: go.Figure,
                                  requirements: List[Dict[str, Any]]) -> None:
        """Add requirements status breakdown to dashboard"""
        # Count requirements by status
        status_counts = {}
        for req in requirements:
            status = req['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        fig.add_trace(go.Pie(
            labels=list(status_counts.keys()),
            values=list(status_counts.values()),
            domain={'x': [0.6, 1], 'y': [0.5, 1]},
            name="Requirements Status"
        ))
    
    def _add_timeline(self,
                     fig: go.Figure,
                     timeline_data: Dict[str, Any]) -> None:
        """Add implementation timeline to dashboard"""
        df = pd.DataFrame(timeline_data['milestones'])
        
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['milestone'],
            mode='markers+text',
            text=df['milestone'],
            textposition="top center",
            domain={'x': [0, 1], 'y': [0, 0.4]},
            name="Implementation Timeline"
        ))
    
    def _create_edge_trace(self,
                          G: nx.DiGraph,
                          pos: Dict) -> go.Scatter:
        """Create edge trace for network visualization"""
        edge_x = []
        edge_y = []
        
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        return go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
    
    def _create_node_trace(self,
                          G: nx.DiGraph,
                          pos: Dict) -> go.Scatter:
        """Create node trace for network visualization"""
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(
                f"ID: {node}<br>"
                f"Status: {G.nodes[node]['status']}<br>"
                f"Priority: {G.nodes[node]['priority']}<br>"
                f"Description: {G.nodes[node]['description']}"
            )
            node_color.append(
                list(self.status_colors.values()).index(
                    self.status_colors[G.nodes[node]['status']]
                )
            )
        
        return go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers',
            hoverinfo='text',
            text=node_text,
            marker=dict(
                showscale=True,
                colorscale='YlOrRd',
                color=node_color,
                size=10,
                colorbar=dict(
                    thickness=15,
                    title='Node Status',
                    xanchor='left',
                    titleside='right'
                ),
                line_width=2
            )
        )
    
    def _prepare_risk_matrix(self,
                            risks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare risk matrix data"""
        impact_levels = sorted(set(risk['impact'] for risk in risks))
        likelihood_levels = sorted(set(risk['likelihood'] for risk in risks))
        
        # Create matrix
        matrix = [[0 for _ in range(len(likelihood_levels))] 
                 for _ in range(len(impact_levels))]
        
        # Fill matrix with risk counts
        for risk in risks:
            i = impact_levels.index(risk['impact'])
            j = likelihood_levels.index(risk['likelihood'])
            matrix[i][j] += 1
        
        return {
            'values': matrix,
            'impact_levels': impact_levels,
            'likelihood_levels': likelihood_levels
        }