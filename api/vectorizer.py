import requests
from io import BytesIO
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import hashlib
import os
from dotenv import load_dotenv
import pdfplumber
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import numpy as np

# Load environment variables
load_dotenv()

# Global variables for lazy loading
_pc = None
_index = None
_model = None

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

def get_namespace_name(doc_id: str) -> str:
    """Generate a consistent namespace name for each document."""
    return f"pdf_chunks_{doc_id}"

# -----------------------------
# PDF processing
# -----------------------------
def process_and_store_pdf(pdf_link: str, doc_id: str = None) -> str:
    """
    Download PDF, extract text, display it, split into chunks, embed, and store in Pinecone.
    Returns the namespace name.
    """
    try:
        if doc_id is None:
            doc_id = f"doc_{hashlib.sha256(pdf_link.encode()).hexdigest()[:16]}"
        
        namespace_name = get_namespace_name(doc_id)
        stats = get_pinecone_index().describe_index_stats()
        if namespace_name in stats.get("namespaces", {}):
            return namespace_name
        headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/115.0 Safari/537.36",
    "Referer": "https://rbi.org.in/",
    "Accept": "application/pdf",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
         } 
        response = requests.get(pdf_link, headers=headers)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower():
            return None, None
        pdf_file = BytesIO(response.content)  # Keep PDF in memory

        text = ""
        tables = []
        with pdfplumber.open(pdf_file) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

                page_tables = page.extract_tables()
                for t in page_tables:
                    tables.append(t)
        text_splitter = RecursiveCharacterTextSplitter(
                      chunk_size=1000,
                      chunk_overlap=200,
                      separators=["\n\n", "\n", " ", ""]
                         )
        text_chunks = text_splitter.create_documents([text])
        table_chunks = []
        for idx, table in enumerate(tables):
            # Replace None values with empty strings in each row
            cleaned_table = [[cell if cell is not None else "" for cell in row] for row in table if row]
            table_str = "\n".join([", ".join(row) for row in cleaned_table])
            table_chunks.append(f"TABLE_{idx}:\n{table_str}")

        # Final list of chunks
        all_chunks = text_chunks + [Document(page_content=t) for t in table_chunks]
        vectors = []
        for i, chunk in enumerate(all_chunks):
            embedding = get_sentence_transformer().encode(chunk.page_content).tolist()
            vectors.append({
                "id": f"{doc_id}_chunk_{i}",
                "values": embedding,
                "metadata": {"text": chunk.page_content, "doc_id": doc_id}
            })
        get_pinecone_index().upsert(vectors=vectors, namespace=namespace_name)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {e}")
        raise
    except Exception as e:
        print(f"Error processing PDF: {e}")
        raise


def vectorize_pdf(pdf_path: str, doc_id: str):
    """
    Extract text from PDF, chunk it, vectorize with SentenceTransformer,
    and store in Pinecone with doc_id as namespace.
    """
    try:
        # Lazy load models
        model = get_sentence_transformer()
        index = get_pinecone_index()
        
        # Extract text from PDF
        text_content = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"

        if not text_content.strip():
            return {"error": "No text content found in PDF"}

        # Chunk the text (simple approach: split by paragraphs or fixed size)
        chunks = chunk_text(text_content)
        
        if not chunks:
            return {"error": "No chunks created from PDF text"}

        # Vectorize each chunk and prepare for Pinecone
        vectors_to_upsert = []
        for i, chunk in enumerate(chunks):
            # Create embedding
            embedding = model.encode(chunk)
            
            # Convert numpy array to list if needed
            if isinstance(embedding, np.ndarray):
                embedding = embedding.astype(float).tolist()
            
            # Create unique ID for this chunk
            chunk_id = f"{doc_id}_chunk_{i}"
            
            # Prepare vector with metadata
            vector_data = {
                "id": chunk_id,
                "values": embedding,
                "metadata": {
                    "text": chunk,
                    "doc_id": doc_id,
                    "chunk_index": i
                }
            }
            vectors_to_upsert.append(vector_data)

        # Upsert to Pinecone using doc_id as namespace
        namespace = f"pdf_chunks_{doc_id}"
        index.upsert(vectors=vectors_to_upsert, namespace=namespace)
        
        return {
            "success": True,
            "chunks_processed": len(chunks),
            "namespace": namespace,
            "doc_id": doc_id
        }
        
    except Exception as e:
        return {"error": f"Error processing PDF: {str(e)}"}

def chunk_text(text):
    # Simple chunking approach: split by paragraphs
    chunks = text.split("\n\n")
    return chunks

get_collection_name = get_namespace_name
