from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from langchain.tools import StructuredTool
import os
from dotenv import load_dotenv
import numpy as np

# Load environment variables
load_dotenv()

# Global variables for lazy loading
_llm = None
_pc = None
_index = None
_model = None

def get_llm():
    """Lazy load ChatOpenAI model"""
    global _llm
    if _llm is None:
        print("🔄 Loading ChatOpenAI model...")
        _llm = ChatOpenAI(
            model="openai/gpt-3.5-turbo",
            api_key=os.getenv("OPEN_ROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "FinCompliance AI"
            }
        )
        print("✅ ChatOpenAI model loaded")
    return _llm

def get_pinecone_client():
    """Lazy load Pinecone client"""
    global _pc
    if _pc is None:
        print("🔄 Loading Pinecone client...")
        _pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        print("✅ Pinecone client loaded")
    return _pc

def get_pinecone_index():
    """Lazy load Pinecone index"""
    global _index
    if _index is None:
        print("🔄 Loading Pinecone index...")
        pc = get_pinecone_client()
        _index = pc.Index("fincompilance")
        print("✅ Pinecone index loaded")
    return _index

def get_sentence_transformer():
    """Lazy load SentenceTransformer model"""
    global _model
    if _model is None:
        print("🔄 Loading SentenceTransformer model...")
        _model = SentenceTransformer('all-mpnet-base-v2')
        print("✅ SentenceTransformer model loaded")
    return _model


def retrieve_document_content(query: str, doc_id: str, top_k: int = 5):
    """
    Retrieve document content from Pinecone using doc_id as namespace.
    """
    try:
        # Lazy load models
        model = get_sentence_transformer()
        index = get_pinecone_index()
        
        # Encode query into embeddings
        query_embedding = model.encode(query)
        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.astype(float).tolist()

        # Query Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=int(top_k),             # ensure Python int
            include_metadata=True,
            namespace=str(doc_id)         # ensure Python str
        )

        matches = results.get("matches", [])
        context_chunks = [m["metadata"].get("text", "") for m in matches]
        return "\n\n---\n\n".join(context_chunks) if context_chunks else "No relevant content found."

    except Exception as e:
        return f"Error retrieving document content: {e}"


def ask_workflow_question(user_question: str, doc_ids: list, doc_titles: list):
    """
    Workflow agent where the LLM chooses the right doc_id based on titles.
    If user asks for documentation/report, a Word file is created and returned separately.
    """

    # Build document catalog with actual doc_ids
    doc_catalog_items = []
    for doc_id, title in zip(doc_ids, doc_titles):
        doc_catalog_items.append(f"{doc_id}: {title}")
    
    doc_catalog = "\n".join(doc_catalog_items)
     
    workflow_system_prompt = f"""You are FinCompliance AI, an RBI regulations expert.

Documents available:
{doc_catalog}

Instructions:
- Choose relevant doc_id(s) based on title
- Use retrieve_document_content tool with chosen doc_id
- Answer user queries using retrieved content
- Only use listed doc_ids
"""


    messages = [
        {"role": "system", "content": workflow_system_prompt},
        {"role": "user", "content": user_question}
    ]

    # Define tools
    workflow_tools = [
        StructuredTool.from_function(
            func=retrieve_document_content,
            name="retrieve_document_content",
            description="Retrieve content from a document using its doc_id. Input: query, doc_id."
        )
    ]

    # Lazy load LLM
    llm = get_llm()
    
    workflow_agent = create_react_agent(llm, workflow_tools)
    response = workflow_agent.invoke({"messages": messages})

    # Extract final LLM answer
    agent_message = response["messages"][-1].content

    return {
        "answer_text": agent_message
    }

