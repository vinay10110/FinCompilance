from typing import Dict, Any, List
import pdfkit
import os
from datetime import datetime
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
import json

class PDFExporter:
    def __init__(self, template_dir: str = "templates"):
        self.template_dir = template_dir
        os.makedirs(template_dir, exist_ok=True)
        self._create_default_templates()
        self.env = Environment(loader=FileSystemLoader(template_dir))
    
    def export_compliance_report(self,
                               data: Dict[str, Any],
                               output_path: str,
                               include_visualizations: bool = True) -> str:
        """Export compliance report to PDF"""
        template = self.env.get_template("compliance_report.html")
        
        # Prepare context with formatted data
        context = self._prepare_compliance_context(data)
        
        # Generate HTML
        html_content = template.render(**context)
        
        # Convert to PDF
        return self._html_to_pdf(html_content, output_path)
    
    def export_implementation_plan(self,
                                 data: Dict[str, Any],
                                 output_path: str,
                                 include_visualizations: bool = True) -> str:
        """Export implementation plan to PDF"""
        template = self.env.get_template("implementation_plan.html")
        
        # Prepare context with formatted data
        context = self._prepare_implementation_context(data)
        
        # Generate HTML
        html_content = template.render(**context)
        
        # Convert to PDF
        return self._html_to_pdf(html_content, output_path)
    
    def _create_default_templates(self):
        """Create default HTML templates if they don't exist"""
        templates = {
            "compliance_report.html": self._get_compliance_template(),
            "implementation_plan.html": self._get_implementation_template(),
            "base.html": self._get_base_template()
        }
        
        for name, content in templates.items():
            path = os.path.join(self.template_dir, name)
            if not os.path.exists(path):
                with open(path, "w") as f:
                    f.write(content)
    
    def _html_to_pdf(self, html_content: str, output_path: str) -> str:
        """Convert HTML content to PDF"""
        # Add custom CSS for PDF styling
        css = CSS(string='''
            @page {
                size: letter;
                margin: 1.5cm;
            }
            body {
                font-family: Arial, sans-serif;
            }
            .page-break {
                page-break-after: always;
            }
        ''')
        
        # Generate PDF
        HTML(string=html_content).write_pdf(
            output_path,
            stylesheets=[css]
        )
        
        return output_path
    
    def _prepare_compliance_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for compliance report template"""
        return {
            "title": "Regulatory Compliance Report",
            "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "compliance_score": data["compliance_score"],
            "status": data["status"],
            "requirements": self._format_requirements(data["requirements_status"]),
            "issues": self._format_issues(data["issues"]),
            "verification_date": data["verification_date"],
            "reviewer": data.get("reviewer", "Automated System"),
            "evidence": self._format_evidence(data.get("evidence", {}))
        }
    
    def _prepare_implementation_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for implementation plan template"""
        return {
            "title": "Implementation Plan",
            "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "document_id": data["document_id"],
            "status": data["status"],
            "tasks": self._format_tasks(data["tasks"]),
            "timeline": self._format_timeline(data["timeline"]),
            "resources": self._format_resources(data["resources"]),
            "risks": self._format_risks(data["risk_assessment"]),
            "total_hours": data["total_estimated_hours"]
        }
    
    def _format_requirements(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format requirements data for template"""
        formatted = []
        for req_id, data in requirements.items():
            formatted.append({
                "id": req_id,
                "status": data["status"],
                "description": data.get("description", ""),
                "priority": data.get("priority", "medium"),
                "findings": data.get("findings", []),
                "evidence": data.get("evidence", "")
            })
        return formatted
    
    def _format_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format issues data for template"""
        return sorted(issues, key=lambda x: {
            'critical': 0,
            'major': 1,
            'minor': 2
        }[x['severity']])
    
    def _format_evidence(self, evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format evidence data for template"""
        formatted = []
        for key, data in evidence.items():
            formatted.append({
                "type": data["type"],
                "description": data.get("description", ""),
                "timestamp": data["timestamp"],
                "artifacts": data.get("artifacts", [])
            })
        return formatted
    
    def _format_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format tasks data for template"""
        return sorted(tasks, key=lambda x: x.get('start_date', ''))
    
    def _format_timeline(self, timeline: Dict[str, Any]) -> Dict[str, Any]:
        """Format timeline data for template"""
        return {
            "phases": timeline.get("phases", []),
            "milestones": timeline.get("milestones", []),
            "dependencies": timeline.get("dependencies", [])
        }
    
    def _format_resources(self, resources: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format resources data for template"""
        formatted = []
        for role, assignments in resources.items():
            for resource in assignments:
                formatted.append({
                    "role": role,
                    "name": resource["name"],
                    "allocation": resource.get("allocation", "100%"),
                    "skills": resource.get("skills", [])
                })
        return formatted
    
    def _format_risks(self, risks: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format risks data for template"""
        formatted = []
        for risk, details in risks.items():
            formatted.append({
                "name": risk,
                "impact": details["impact"],
                "likelihood": details["likelihood"],
                "category": details["category"],
                "mitigation": details.get("mitigation", "")
            })
        return sorted(formatted, key=lambda x: -(x["impact"] * x["likelihood"]))
    
    def _get_base_template(self) -> str:
        """Get base HTML template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{% block title %}{% endblock %}</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .section {
                    margin-bottom: 20px;
                }
                .table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 15px;
                }
                .table th, .table td {
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }
                .table th {
                    background-color: #f5f5f5;
                }
                .status {
                    font-weight: bold;
                }
                .status-compliant { color: green; }
                .status-non-compliant { color: red; }
                .status-partial { color: orange; }
                .page-break { page-break-after: always; }
            </style>
        </head>
        <body>
            {% block content %}{% endblock %}
        </body>
        </html>
        """
    
    def _get_compliance_template(self) -> str:
        """Get compliance report template"""
        return """
        {% extends "base.html" %}
        
        {% block title %}{{ title }}{% endblock %}
        
        {% block content %}
        <div class="header">
            <h1>{{ title }}</h1>
            <p>Generated on: {{ generated_date }}</p>
        </div>
        
        <div class="section">
            <h2>Executive Summary</h2>
            <p>Compliance Score: <strong>{{ compliance_score }}%</strong></p>
            <p>Status: <span class="status">{{ status }}</span></p>
            <p>Verification Date: {{ verification_date }}</p>
            <p>Reviewer: {{ reviewer }}</p>
        </div>
        
        <div class="section page-break">
            <h2>Requirements Status</h2>
            <table class="table">
                <tr>
                    <th>ID</th>
                    <th>Status</th>
                    <th>Description</th>
                    <th>Priority</th>
                </tr>
                {% for req in requirements %}
                <tr>
                    <td>{{ req.id }}</td>
                    <td class="status status-{{ req.status }}">{{ req.status }}</td>
                    <td>{{ req.description }}</td>
                    <td>{{ req.priority }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        
        {% if issues %}
        <div class="section page-break">
            <h2>Issues Found</h2>
            <table class="table">
                <tr>
                    <th>Severity</th>
                    <th>Description</th>
                    <th>Recommendation</th>
                </tr>
                {% for issue in issues %}
                <tr>
                    <td>{{ issue.severity }}</td>
                    <td>{{ issue.description }}</td>
                    <td>{{ issue.recommendation }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        {% endif %}
        
        {% if evidence %}
        <div class="section">
            <h2>Evidence</h2>
            <table class="table">
                <tr>
                    <th>Type</th>
                    <th>Description</th>
                    <th>Timestamp</th>
                </tr>
                {% for item in evidence %}
                <tr>
                    <td>{{ item.type }}</td>
                    <td>{{ item.description }}</td>
                    <td>{{ item.timestamp }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        {% endif %}
        {% endblock %}
        """
    
    def _get_implementation_template(self) -> str:
        """Get implementation plan template"""
        return """
        {% extends "base.html" %}
        
        {% block title %}{{ title }}{% endblock %}
        
        {% block content %}
        <div class="header">
            <h1>{{ title }}</h1>
            <p>Generated on: {{ generated_date }}</p>
        </div>
        
        <div class="section">
            <h2>Plan Overview</h2>
            <p>Document ID: {{ document_id }}</p>
            <p>Status: {{ status }}</p>
            <p>Total Estimated Hours: {{ total_hours }}</p>
        </div>
        
        <div class="section page-break">
            <h2>Tasks</h2>
            <table class="table">
                <tr>
                    <th>Title</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Assigned To</th>
                    <th>Hours</th>
                </tr>
                {% for task in tasks %}
                <tr>
                    <td>{{ task.title }}</td>
                    <td>{{ task.type }}</td>
                    <td>{{ task.status }}</td>
                    <td>{{ task.assigned_to }}</td>
                    <td>{{ task.estimated_hours }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        
        <div class="section page-break">
            <h2>Resource Allocation</h2>
            <table class="table">
                <tr>
                    <th>Role</th>
                    <th>Name</th>
                    <th>Allocation</th>
                    <th>Skills</th>
                </tr>
                {% for resource in resources %}
                <tr>
                    <td>{{ resource.role }}</td>
                    <td>{{ resource.name }}</td>
                    <td>{{ resource.allocation }}</td>
                    <td>{{ resource.skills|join(', ') }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        
        <div class="section">
            <h2>Risk Assessment</h2>
            <table class="table">
                <tr>
                    <th>Risk</th>
                    <th>Impact</th>
                    <th>Likelihood</th>
                    <th>Category</th>
                    <th>Mitigation</th>
                </tr>
                {% for risk in risks %}
                <tr>
                    <td>{{ risk.name }}</td>
                    <td>{{ risk.impact }}</td>
                    <td>{{ risk.likelihood }}</td>
                    <td>{{ risk.category }}</td>
                    <td>{{ risk.mitigation }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        {% endblock %}
        """