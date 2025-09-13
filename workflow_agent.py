from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from langchain.tools import StructuredTool
import os
from dotenv import load_dotenv
from docx import Document
from io import BytesIO
import base64
import numpy as np

# Load environment variables
load_dotenv()

llm = ChatOpenAI(
    model="openai/gpt-3.5-turbo",
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "FinCompliance AI"
    }
)

# Init Pinecone + embeddings
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("fincompilance")
model = SentenceTransformer('all-mpnet-base-v2')


def retrieve_document_content(query: str, doc_id: str, top_k: int = 5):
    """
    Retrieve document content from Pinecone using doc_id as namespace.
    """
    try:
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

    workflow_agent = create_react_agent(llm, workflow_tools)
    response = workflow_agent.invoke({"messages": messages})

    # Extract final LLM answer
    agent_message = response["messages"][-1].content

    return {
        "answer_text": agent_message
    }

