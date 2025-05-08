from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import uvicorn
import sys
import os
from pathlib import Path
from fastapi.security import OAuth2PasswordBearer

# Add parent directory to path to import from src
sys.path.append(str(Path(__file__).parent.parent))

from app import ComplianceAutomationSystem
import asyncio
import json
from datetime import datetime

app = FastAPI(
    title="Regulatory Compliance Automation API",
    description="API for automating regulatory compliance processes",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize compliance system
compliance_system = ComplianceAutomationSystem()

class ProcessResponse(BaseModel):
    status: str
    change_analysis: Dict[str, Any] = None
    implementation_plan: Dict[str, Any] = None
    compliance_status: Dict[str, Any] = None
    error: str = None

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/process-document", response_model=ProcessResponse)
async def process_document(file: UploadFile = File(...)):
    """Process a regulatory document and generate compliance analysis"""
    try:
        # Save uploaded file temporarily
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"rbi_updates/uploaded_{timestamp}_{file.filename}"
        
        os.makedirs("rbi_updates", exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process the document
        result = await compliance_system.process_regulatory_update(file_path)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return ProcessResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results/{result_id}")
async def get_result(result_id: str):
    """Retrieve a specific analysis result"""
    try:
        results_dir = "results"
        result_file = f"{results_dir}/workflow_state_{result_id}.json"
        
        if not os.path.exists(result_file):
            raise HTTPException(status_code=404, detail="Result not found")
        
        with open(result_file, "r") as f:
            result = json.load(f)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results")
async def list_results():
    """List all available analysis results"""
    try:
        results_dir = "results"
        if not os.path.exists(results_dir):
            return []
        
        results = []
        for file in os.listdir(results_dir):
            if file.startswith("workflow_state_"):
                result_id = file.replace("workflow_state_", "").replace(".json", "")
                with open(os.path.join(results_dir, file), "r") as f:
                    data = json.load(f)
                    results.append({
                        "id": result_id,
                        "timestamp": result_id.split("_")[0],
                        "status": data.get("current_phase", "unknown"),
                        "has_implementation_plan": bool(data.get("implementation_plan")),
                        "has_compliance_status": bool(data.get("compliance_status"))
                    })
        
        return sorted(results, key=lambda x: x["timestamp"], reverse=True)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Handle chat interactions with the compliance system"""
    try:
        # Process the message through the compliance system
        response = await compliance_system.process_chat_message(request.message)
        return ChatResponse(response=response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_api():
    """Start the FastAPI server"""
    uvicorn.run(app, host="0.0.0.0", port=8000)