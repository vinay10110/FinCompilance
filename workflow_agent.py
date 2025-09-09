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
        print(context_chunks)
        return "\n\n---\n\n".join(context_chunks) if context_chunks else "No relevant content found."

    except Exception as e:
        return f"Error retrieving document content: {e}"


def create_document_tool(content: str, filename: str = "compliance_report.docx"):
    """
    Create a Word document with the given content and return Base64 for frontend download.
    """
    try:
        doc = Document()
        doc.add_heading("FinCompliance AI Report", 0)
        doc.add_paragraph(content)

        # Save to BytesIO instead of disk
        file_stream = BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)

        encoded_doc = base64.b64encode(file_stream.read()).decode("utf-8")
        return {"filename": filename, "content_base64": encoded_doc}

    except Exception as e:
        return {"error": str(e)}


def ask_workflow_question(user_question: str, doc_ids: list, doc_titles: list):
    """
    Workflow agent where the LLM chooses the right doc_id based on titles.
    If user asks for documentation/report, a Word file is created and returned separately.
    """

    # Build document catalog
    doc_catalog = "\n".join([f"- {doc_id}: {title}" for doc_id, title in zip(doc_ids, doc_titles)])
    print(doc_catalog)
    workflow_system_prompt = f"""
You are FinCompliance AI, an expert in RBI regulations.

You have access to these workflow documents:
{doc_catalog}

When answering user questions:
- Decide which document(s) are relevant based on their title.
- Call the `retrieve_document_content` tool with the chosen doc_id.
- Use the retrieved content to provide your analysis.
- If the user asks for a report, call the `create_document` tool.
- Do NOT invent doc_ids; only use the ones listed.
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
        ),
        StructuredTool.from_function(
            func=create_document_tool,
            name="create_document",
            description="Create a Word document report from provided content."
        )
    ]

    workflow_agent = create_react_agent(llm, workflow_tools)
    response = workflow_agent.invoke({"messages": messages})

    # Extract final LLM answer
    agent_message = response["messages"][-1].content
    document = None

    # 🔍 Look for structured tool output
    if isinstance(agent_message, dict) and "filename" in agent_message and "content_base64" in agent_message:
        # Pure document response
        document = agent_message
        agent_message = None
    else:
        # Sometimes LLM may mix JSON into text → try regex parse
        import re, json
        doc_match = re.search(r'\{[^}]*"filename"[^}]*"content_base64"[^}]*\}', str(agent_message))
        if doc_match:
            try:
                document = json.loads(doc_match.group())
                agent_message = str(agent_message).replace(doc_match.group(), "").strip()
            except Exception:
                pass

    return {
        "answer_text": agent_message,   # normal chat answer
        "document": document            # if a doc was generated
    }

