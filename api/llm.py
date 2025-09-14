from langchain_openai import ChatOpenAI  
from langgraph.prebuilt import create_react_agent
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from langchain.tools import StructuredTool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global variables for lazy loading
_llm = None
_pc = None
_index = None
_model = None
_agent_executor = None
_tools = None

system_prompt = """
You are FinCompliance AI, an expert assistant specialized in interpreting and explaining RBI (Reserve Bank of India) guidelines, notifications, and regulatory documents.  

Your role is to:
- Answer user questions strictly based on the retrieved document context provided from Pinecone.
- If the retrieved content is insufficient or unclear, state clearly: "The available RBI document context does not fully answer this question." Then suggest where the user might look in the RBI framework.
- Always cite the relevant RBI section, circular, or paragraph when possible.
- Provide clear, structured, and compliance-focused answers, avoiding speculation or assumptions.
- Use professional, regulatory-compliant language. Be precise and concise.
- Do NOT invent rules, regulations, or compliance procedures beyond the provided RBI documents.

Remember:
- The user is asking compliance-related questions.
- Your job is to help them understand what the RBI documents actually say, not to provide legal advice.
- Keep answers factual, grounded, and aligned with official RBI terminology.
"""

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

def pinecone_query_tool(query: str, namespace: str, top_k: int = 5):
    """
    Encode query with sentence-transformers, search Pinecone, and return top results.
    """
    try:
        # Lazy load models
        model = get_sentence_transformer()
        index = get_pinecone_index()
        
        # Encode the query into an embedding
        query_embedding = model.encode(query).tolist()

        # Query Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            namespace=namespace
        )

        matches = results.get("matches", [])
        context_chunks = [m["metadata"].get("text", "") for m in matches]

        return "\n\n---\n\n".join(context_chunks)

    except Exception as e:
        print(f" Error while querying: {e}")
        raise

def get_tools():
    """Lazy load tools"""
    global _tools
    if _tools is None:
        _tools = [
            StructuredTool.from_function(
                func=pinecone_query_tool,
                name="pinecone_query",
                description="Query Pinecone with a natural language question and a namespace (document ID). Returns top matching text chunks."
            )
        ]
    return _tools

def get_agent_executor():
    """Lazy load React agent"""
    global _agent_executor
    if _agent_executor is None:
        print("🔄 Creating React agent...")
        llm = get_llm()
        tools = get_tools()
        _agent_executor = create_react_agent(llm, tools)
        print("✅ React agent created")
    return _agent_executor

def ask_doc_question(user_question: str, doc_id: str, top_k: int = 5):
    """
    Run an agent query with user input and specific doc_id (namespace).
    """
    # Lazy load agent
    agent_executor = get_agent_executor()
    
    # Build messages properly for ChatOpenAI
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Question: {user_question}\nUse namespace: pdf_chunks_{doc_id}\nReturn relevant context."}
    ]
    response = agent_executor.invoke({"messages": messages})
    result = response["messages"][-1].content
    return result
