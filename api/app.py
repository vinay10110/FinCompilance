import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor

# Fix for Windows event loop policy
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from vectorizer import process_and_store_pdf
from dotenv import load_dotenv
from neon_database import db
import traceback
from llm import ask_doc_question
from circulars_scrapper import scrape_and_save_circulars
from press_scrapper import scrape_and_save_press_releases
from workflow_agent import ask_workflow_question

# Load environment variables
load_dotenv()

# Pydantic models for request/response validation
class VectorizeRequest(BaseModel):
    doc_id: str
    pdf_link: str

class MessageRequest(BaseModel):
    message: str
    role: str
    user_id: Optional[str] = "default_user"

class ProcessMessageRequest(BaseModel):
    message: str
    doc_id: Optional[str] = None

class StandardResponse(BaseModel):
    status: str
    message: Optional[str] = None
    updates: Optional[List[Dict[str, Any]]] = None
    response: Optional[Dict[str, Any]] = None
    messages: Optional[List[Dict[str, Any]]] = None
    data: Optional[Dict[str, Any]] = None


class CreateWorkflowRequest(BaseModel):
    user_id: str
    name: Optional[str] = None
    description: Optional[str] = None

class AddDocumentToWorkflowRequest(BaseModel):
    doc_type: str  
    doc_id: str

class WorkflowChatRequest(BaseModel):
    query: str
    doc_ids: List[str]
    doc_titles: List[str]

class WorkflowChatHistoryRequest(BaseModel):
    workflow_id: str
    user_id: str
    limit: Optional[int] = 50

class SaveWorkflowChatMessageRequest(BaseModel):
    workflow_id: str
    user_id: str
    role: str 
    content: str
    document_data: Optional[Dict[str, Any]] = None

class RemoveDocumentFromWorkflowRequest(BaseModel):
    doc_type: str  
    doc_id: int 

class DeleteWorkflowRequest(BaseModel):
    user_id: str  

try:
    print("Initializing database connection...")
    if db.connect():
        print("Database connection established")
except Exception as e:
    print(f"❌ Error initializing database: {str(e)}")


app = FastAPI()

# -----------------------
# Startup Scraping Functions
# -----------------------

@app.on_event("startup")
async def startup_event():
    """Run one-time scraping on application startup"""
    print("🚀 Application starting up...")
    
    try:
        # Run one-time scraping in thread pool
        print("🔄 Running startup data scraping...")
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=2)
        
        # Scrape circulars
        print("📄 Scraping RBI circulars...")
        circulars_result = await loop.run_in_executor(executor, scrape_and_save_circulars)
        print(f"✅ Found {len(circulars_result)} new circulars")
        
        # Scrape press releases
        print("📰 Scraping RBI press releases...")
        press_releases_result = await loop.run_in_executor(executor, scrape_and_save_press_releases)
        print(f"✅ Found {len(press_releases_result)} new press releases")
        
        print("✅ Startup scraping completed successfully")
        print("📊 Application ready to serve requests")
        
    except Exception as e:
        print(f"❌ Error during startup scraping: {str(e)}")
        import traceback
        print(f"Detailed error: {traceback.format_exc()}")
        print("⚠️ Application will continue without initial scraping data")

# -----------------------
# Middleware
# -----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/get_updates", response_model=StandardResponse)
async def get_updates():
    """
    Route to fetch RBI press release updates from Neon DB
    Returns a list of updates with their details
    """
    try:
        updates = db.get_latest_press_releases()
        return StandardResponse(
            status="success",
            updates=updates
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch updates: {str(e)}"
        )


@app.post("/vectorize", response_model=StandardResponse)
async def vectorize_document(data: VectorizeRequest):
    """
    Process and store a document in ChromaDB when user clicks Pull & Chat
    """
    try:
        process_and_store_pdf(data.pdf_link, data.doc_id)
        
        return StandardResponse(
            status="success",
            message="Document processed and stored successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )

@app.post("/save_message", response_model=StandardResponse)
async def save_message(data: MessageRequest):
    """
    Save a chat message to the database
    """
    try:
        db.save_message(data.user_id, data.role, data.message)
        
        return StandardResponse(
            status="success",
            message="Message saved successfully"
        )
        
    except Exception as e:
        print(f"❌ Error saving message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save message: {str(e)}"
        )

@app.post("/process_message", response_model=StandardResponse)
async def process_message(data: ProcessMessageRequest):
    """
    Process user message and generate AI response using document context
    """
    try:
        if not data.doc_id:
            raise HTTPException(
                status_code=400,
                detail="No doc_id provided"
            )

        # Generate AI response
        try:
            response_content = ask_doc_question(data.message, data.doc_id)
            return StandardResponse(
                status="success",
                response={
                    "content": response_content
                }
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating response: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@app.get("/get_circulars", response_model=StandardResponse)
async def get_circulars(limit: int = 50):
    """
    Get RBI master circulars from database
    Returns latest circulars with category information
    """
    try:
        circulars = db.get_latest_circulars()
        return StandardResponse(
            status="success",
            message=f"Retrieved {len(circulars)} circulars",
            updates=circulars
        )
        
    except Exception as e:
        print(f"❌ Error retrieving circulars: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve circulars: {str(e)}"
        )


@app.get("/getchats", response_model=StandardResponse)
async def get_chat_history(user_id: str = "default_user"):
    """
    Get chat history for a user
    Returns all previous chats between the user and AI
    """
    try:
        chat_history = db.get_user_chat_history(user_id, limit=100)  
        
        formatted_messages = []
        for chat in chat_history:
            formatted_messages.append({
                "content": chat.get("content", ""),
                "isUser": chat.get("role") == "user",
                "message_type": chat.get("role", "assistant"),
                "timestamp": chat.get("created_at", "")
            })
        
        return StandardResponse(
            status="success",
            message=f"Retrieved {len(formatted_messages)} chat messages",
            messages=formatted_messages
        )
        
    except Exception as e:
        import traceback
        print(f"Detailed error: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )


# Workflow routes
@app.post("/workflows", response_model=StandardResponse)
async def create_workflow(data: CreateWorkflowRequest):
    """
    Create a new empty workflow
    """
    try:
        workflow = db.create_workflow(data.user_id, data.name, data.description)
        
        return StandardResponse(
            status="success",
            message="Workflow created successfully",
            data={"workflow": workflow}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create workflow: {str(e)}"
        )

@app.post("/workflows/{workflow_id}/documents", response_model=StandardResponse)
async def add_document_to_workflow(workflow_id: str, data: AddDocumentToWorkflowRequest):
    """
    Add a document to an existing workflow (vectorizes first, then adds)
    """
    try:
        
        # Convert doc_id hash to database primary key ID
        if data.doc_type == 'press_release':
            db_id = db.get_press_release_id_by_doc_id(data.doc_id)
            
        elif data.doc_type == 'circular':
            db_id = db.get_circular_id_by_doc_id(data.doc_id)

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid doc_type: {data.doc_type}. Must be 'press_release' or 'circular'"
            )
        
        if db_id is None:
            print(f"❌ Document not found with doc_id: {data.doc_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Document not found with doc_id: {data.doc_id}"
            )
        
        # Get document details to extract PDF link for vectorization
        document_details = db.get_document_by_type_and_id(data.doc_type, db_id)
        if not document_details:
            raise HTTPException(
                status_code=404,
                detail=f"Document details not found for {data.doc_type} with id: {db_id}"
            )
        
        pdf_link = document_details.get('pdf_link')
        if not pdf_link:
            raise HTTPException(
                status_code=400,
                detail=f"Document does not have a PDF link for vectorization"
            )
        
        # Vectorize the document first
        try:
            process_and_store_pdf(pdf_link, data.doc_id)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to vectorize document: {str(e)}"
            )
        
        # Now add to workflow
        document = db.add_document_to_workflow(workflow_id, data.doc_type, db_id)
        
        if document is None:
            return StandardResponse(
                status="success",
                message="Document already exists in workflow",
                data={"document": None}
            )
        
        return StandardResponse(
            status="success",
            message="Document vectorized and added to workflow successfully",
            data={"document": document}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add document to workflow: {str(e)}"
        )

@app.get("/workflows/{workflow_id}", response_model=StandardResponse)
async def get_workflow(workflow_id: str):
    """
    Get workflow with its linked documents
    """
    try:
        workflow = db.get_workflow_with_documents(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=404,
                detail="Workflow not found"
            )
        
        return StandardResponse(
            status="success",
            message="Workflow retrieved successfully",
            data={"workflow": workflow}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve workflow: {str(e)}"
        )

@app.get("/workflows", response_model=StandardResponse)
async def get_user_workflows(user_id: str, limit: int = 50):
    """
    Get all workflows for a user
    """
    try:
        workflows = db.get_user_workflows(user_id, limit)
        
        return StandardResponse(
            status="success",
            message=f"Retrieved {len(workflows)} workflows",
            data={"workflows": workflows}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve workflows: {str(e)}"
        )

@app.get("/documents/{doc_type}/{doc_id}", response_model=StandardResponse)
async def get_document_details(doc_type: str, doc_id: int):
    """
    Get document details by doc_type and database ID
    """
    try:
        if doc_type not in ['press_release', 'circular']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid doc_type: {doc_type}. Must be 'press_release' or 'circular'"
            )
        
        document = db.get_document_by_type_and_id(doc_type, doc_id)
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found with doc_type: {doc_type} and id: {doc_id}"
            )
        
        return StandardResponse(
            status="success",
            message="Document retrieved successfully",
            data={"document": document}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve document: {str(e)}"
        )

@app.post("/workflows/{workflow_id}/chat", response_model=StandardResponse)
async def workflow_chat(workflow_id: str, data: WorkflowChatRequest, user_id: str):
    """
    Process workflow chat message using workflow-specific documents and save to database
    """
    try:
        
        if not data.doc_ids or not data.doc_titles:
            raise HTTPException(
                status_code=400,
                detail="No documents provided for workflow chat"
            )
        
        if len(data.doc_ids) != len(data.doc_titles):
            raise HTTPException(
                status_code=400,
                detail="Mismatch between doc_ids and doc_titles count"
            )
        
        db.save_workflow_chat_message(
            workflow_id=workflow_id,
            user_id=user_id,
            role="user",
            content=data.query,
            document_data=None
        )
        
        # Call workflow agent
        response = ask_workflow_question(data.query, data.doc_ids, data.doc_titles)
        
        # Save assistant response to database
        db.save_workflow_chat_message(
            workflow_id=workflow_id,
            user_id=user_id,
            role="assistant",
            content=response["answer_text"],
            document_data=response.get("document")
        )
        
        return StandardResponse(
            status="success",
            message="Workflow chat response generated successfully",
            response={
                "content": response["answer_text"],
                "document": response.get("document")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process workflow chat: {str(e)}"
        )

@app.get("/workflows/{workflow_id}/chat/history", response_model=StandardResponse)
async def get_workflow_chat_history(workflow_id: str, user_id: str, limit: int = 50):
    """
    Get chat history for a specific workflow and user
    """
    try:        
        chat_history = db.get_workflow_chat_history(workflow_id, user_id, limit)
        
        # Convert to frontend format
        messages = []
        for msg in chat_history:
            message = {
                "id": msg["id"],
                "type": msg["role"],
                "content": msg["content"],
                "timestamp": msg["created_at"].isoformat() if msg["created_at"] else None,
                "document": msg["document_data"] if msg["document_data"] else None
            }
            messages.append(message)
        return StandardResponse(
            status="success",
            message=f"Retrieved {len(messages)} chat messages",
            data={"messages": messages}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chat history: {str(e)}"
        )

@app.post("/workflows/{workflow_id}/chat/save", response_model=StandardResponse)
async def save_workflow_chat_message(workflow_id: str, data: SaveWorkflowChatMessageRequest):
    """
    Save a chat message for a specific workflow
    """
    try:       
        saved_message = db.save_workflow_chat_message(
            workflow_id=workflow_id,
            user_id=data.user_id,
            role=data.role,
            content=data.content,
            document_data=data.document_data
        )
        return StandardResponse(
            status="success",
            message="Chat message saved successfully",
            data={"message": saved_message}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save chat message: {str(e)}"
        )

@app.delete("/workflows/{workflow_id}/chat/clear", response_model=StandardResponse)
async def clear_workflow_chat_history(workflow_id: str, user_id: str):
    """
    Clear chat history for a specific workflow and user
    """
    try:
        deleted_count = db.clear_workflow_chat_history(workflow_id, user_id)
        
        return StandardResponse(
            status="success",
            message=f"Cleared {deleted_count} chat messages"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear chat history: {str(e)}"
        )

@app.delete("/workflows/{workflow_id}/documents", response_model=StandardResponse)
async def remove_document_from_workflow(workflow_id: str, data: RemoveDocumentFromWorkflowRequest):
    """
    Remove a document from a workflow
    """
    try:
        success = db.remove_document_from_workflow(workflow_id, data.doc_type, data.doc_id)
        
        if success:
            return StandardResponse(
                status="success",
                message="Document removed from workflow successfully"
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="Document not found in workflow"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove document from workflow: {str(e)}"
        )

@app.delete("/workflows/{workflow_id}", response_model=StandardResponse)
async def delete_workflow(workflow_id: str, data: DeleteWorkflowRequest):
    """
    Delete a workflow and all associated data
    """
    try:
        success = db.delete_workflow(workflow_id, data.user_id)
        
        if success:
            return StandardResponse(
                status="success",
                message="Workflow deleted successfully"
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="Workflow not found or you don't have permission to delete it"
            )
        
    except Exception as e:
        print(f"❌ Error deleting workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete workflow: {str(e)}"
        )

if __name__ == '__main__':
    import uvicorn
    # Use environment variables for production deployment
    host = os.getenv("HOST", "0.0.0.0")  # Bind to all interfaces for Render
    port = int(os.getenv("PORT", 5000))  # Use Render's provided PORT
    reload = os.getenv("ENVIRONMENT", "development") == "development"  # Only reload in dev
    
    uvicorn.run("app:app", host=host, port=port, reload=reload)