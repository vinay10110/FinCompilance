from langchain_openai import ChatOpenAI  
from langchain.agents import Tool
from langgraph.prebuilt import create_react_agent
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from langchain.tools import StructuredTool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

llm = ChatOpenAI(
    model="openai/gpt-3.5-turbo",
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),  
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "FinCompliance AI"
    }
)

# Initialize Pinecone and SentenceTransformer
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("fincompilance")
model = SentenceTransformer('all-mpnet-base-v2')

def pinecone_query_tool(query: str, namespace: str, top_k: int = 5):
    """
    Encode query with sentence-transformers, search Pinecone, and return top results.
    """
    try:
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

tools = [
    StructuredTool.from_function(
        func=pinecone_query_tool,
        name="pinecone_query",
        description="Query Pinecone with a natural language question and a namespace (document ID). Returns top matching text chunks."
    )
]
# 3. Create a React agent with LangGraph
agent_executor = create_react_agent(llm, tools)

def ask_doc_question(user_question: str, doc_id: str, top_k: int = 5):
    """
    Run an agent query with user input and specific doc_id (namespace).
    """
    # Build messages properly for ChatOpenAI
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Question: {user_question}\nUse namespace: pdf_chunks_{doc_id}\nReturn relevant context."}
    ]
    response = agent_executor.invoke({"messages": messages})
    result = response["messages"][-1].content
    return result
