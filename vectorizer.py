import requests
import PyPDF2
from io import BytesIO
import chromadb
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter
import hashlib
import os

# Initialize ChromaDB
CHROMA_DB_PATH = "./chroma_db"
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# Use sentence-transformers for embeddings
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

def get_collection_name(doc_id: str) -> str:
    """Helper function to generate consistent collection names"""
    return f"pdf_chunks_{doc_id}"

def process_and_store_pdf(pdf_link: str, doc_id: str = None) -> str:
    """
    Download PDF from link, extract text, create chunks, and store in ChromaDB.
    
    Args:
        pdf_link (str): URL of the PDF to process
        doc_id (str, optional): Unique identifier for the document. If None, generates from PDF link
    
    Returns:
        str: Name of the ChromaDB collection where chunks are stored
    """
    try:
        # Generate a consistent collection name from the PDF link if doc_id not provided
        if doc_id is None:
            doc_id = f"doc_{hashlib.sha256(pdf_link.encode()).hexdigest()[:16]}"
        
        collection_name = get_collection_name(doc_id)
        
        # Check if collection already exists
        try:
            collection = chroma_client.get_collection(
                name=collection_name,
                embedding_function=sentence_transformer_ef
            )
            print(f"Collection {collection_name} already exists. Returning existing collection.")
            return collection_name
        except:
            collection = chroma_client.create_collection(
                name=collection_name,
                embedding_function=sentence_transformer_ef
            )

        # Download PDF
        print(f"Downloading PDF from {pdf_link}")
        response = requests.get(pdf_link)
        response.raise_for_status()  # Raise exception for bad status codes
        
        # Read PDF content
        pdf_file = BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        # Create chunks using RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.create_documents([text])
        
        # Prepare chunks for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            documents.append(chunk.page_content)
            metadatas.append({
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "source": pdf_link
            })
            ids.append(chunk_id)
        
        # Add chunks to ChromaDB
        print(f"Adding {len(documents)} chunks to ChromaDB collection {collection_name}")
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        return collection_name
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {str(e)}")
        raise
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        raise

def query_collection(collection_name: str, query: str, n_results: int = 5) -> list:
    """
    Query a ChromaDB collection for relevant chunks.
    
    Args:
        collection_name (str): Name of the collection to query
        query (str): Query text to search for
        n_results (int): Number of results to return
    
    Returns:
        list: List of relevant text chunks with their metadata
    """
    try:
        collection = chroma_client.get_collection(
            name=collection_name,
            embedding_function=sentence_transformer_ef
        )
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return results
        
    except Exception as e:
        print(f"Error querying collection: {str(e)}")
        raise

# Example usage:
# collection_name = process_and_store_pdf("https://example.com/sample.pdf", "doc123")
# results = query_collection(collection_name, "What is the main topic?")