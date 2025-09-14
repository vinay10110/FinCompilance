import requests
from io import BytesIO
from langchain.text_splitter import RecursiveCharacterTextSplitter
import hashlib
import os
from dotenv import load_dotenv
import pdfplumber
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from langchain.schema import Document
# Load environment variables
load_dotenv()

model = SentenceTransformer('all-mpnet-base-v2')
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

index = pc.Index("fincompilance")

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
        stats = index.describe_index_stats()
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
            embedding = model.encode(chunk.page_content).tolist()
            vectors.append({
                "id": f"{doc_id}_chunk_{i}",
                "values": embedding,
                "metadata": {"text": chunk.page_content, "doc_id": doc_id}
            })
        index.upsert(vectors=vectors, namespace=namespace_name)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {e}")
        raise
    except Exception as e:
        print(f"Error processing PDF: {e}")
        raise


get_collection_name = get_namespace_name
