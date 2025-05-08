from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import uvicorn
import sys
import os
from pathlib import Path
from fastapi.security import OAuth2PasswordBearer
from ..srcutils.rbi_scraper import RBIWebScraper

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

# Initialize systems
compliance_system = ComplianceAutomationSystem()
scraper = RBIWebScraper()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class WebScraperResponse(BaseModel):
    status: str
    updates: List[Dict[str, Any]] = []
    error: str = None

class MarkAsReadRequest(BaseModel):
    press_release_link: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Handle chat interactions with the compliance system"""
    try:
        response = await compliance_system.process_chat_message(request.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/updates", response_model=WebScraperResponse)
async def get_updates(background_tasks: BackgroundTasks, new_only: bool = False):
    """Get latest updates and trigger new scraping in background"""
    try:
        # Get stored updates
        updates = scraper.get_updates(new_only=new_only)
        
        # Trigger new scraping in background
        background_tasks.add_task(scraper.scrape)
        
        return WebScraperResponse(
            status="success",
            updates=updates
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/updates/check", response_model=WebScraperResponse)
async def check_updates():
    """Manually trigger update check"""
    try:
        new_updates = scraper.scrape()
        return WebScraperResponse(
            status="success",
            updates=new_updates
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/updates/mark-read")
async def mark_as_read(request: MarkAsReadRequest):
    """Mark an update as read"""
    try:
        scraper.mark_as_read(request.press_release_link)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_api():
    """Start the FastAPI server"""
    uvicorn.run(app, host="0.0.0.0", port=8000)