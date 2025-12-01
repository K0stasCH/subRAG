from langchain_community.document_loaders import SRTLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from typing import List
import re, os
from config import *


def clean_subtitle_text(text):
    # 1. Remove HTML tags (e.g., <i>, </i>, <font color="...">)
    cleaned_text = re.sub(r'<[^>]+>', '', text)
    
    # 2. Remove annotations/sound descriptions in brackets or parentheses
    # (Optional: remove if you only want dialogue)
    cleaned_text = re.sub(r'\[.*?\]', '', cleaned_text) # For [Text in brackets]
    cleaned_text = re.sub(r'\s*\([^)]*\)', '', cleaned_text) # For (Text in parentheses)
    
    # 3. Clean up leading/trailing whitespace and multiple spaces
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text

def save_clean_subs(cleanSubtiltes:str, pathToSave:str)->None:
    try:
        with open(pathToSave, 'w', encoding='utf-8') as f:
            # We save the entire cleaned script as one large block of text
            f.write(cleanSubtiltes)
        
        print("---")
        print(f"✅ Success! Cleaned dialogue saved to: **{pathToSave}**")
        print("---")

    except Exception as e:
        print(f"An error occurred while writing the file: {e}")
    return

def spli_text(documents: List[str], chunk_size: int = 1000, chunk_overlap: int = 200):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,  # A good size for dialogue
        chunk_overlap=chunk_overlap   # Ensures context flow
    )
    split_chunks = text_splitter.split_documents(documents)
    return split_chunks

def get_embeddings(        
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu") -> HuggingFaceEmbeddings:
    """Initializes and returns the local HuggingFace embedding model."""

    print(f"Loading local embedding model: {model_name}")
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': device} 
    )
    return embeddings

def create_and_save_or_load_embeddings(
        chunks: List[Document] | None = None,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
        save_path: str = "index/movie_script_faiss_index"
        ) -> FAISS:
    """
    Creates embeddings from document chunks, builds a FAISS index, 
    saves it locally, and returns the in-memory vector store.
    """
    
    embeddings = get_embeddings(model_name, device)
    if os.path.exists(FAISS_INDEX_PATH) and os.path.isdir(FAISS_INDEX_PATH):
        # 1. LOAD existing index
        print(f"Loading existing FAISS index from: {FAISS_INDEX_PATH}")
        # allow_dangerous_deserialization=True is required by LangChain for security when loading
        vector_store = FAISS.load_local(
            FAISS_INDEX_PATH, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        print("✅ Vector store loaded successfully.")
    
    elif chunks is not None:
        # 2. CREATE new index
        print("Index not found. Creating new FAISS index from document chunks...")
        vector_store = FAISS.from_documents(
            documents=chunks,
            embedding=embeddings
        )
        vector_store.save_local(FAISS_INDEX_PATH)
        print(f"✅ Vector store created and saved to: {FAISS_INDEX_PATH}")
    
    else:
        raise FileNotFoundError(
            "Vector store path not found, and no document chunks were provided to create it."
        )
        
    return vector_store

def main():
    loader = SRTLoader(SRT_PATHS[0])
    docs = loader.load()
    for doc in docs:
        doc.page_content = clean_subtitle_text(doc.page_content)
    split_chunks = spli_text(docs, CHUNK_SIZE, CHUNK_OVERLAP)
    x = create_and_save_or_load_embeddings(split_chunks, HF_EMBEDDING_MODEL, DEVICE, FAISS_INDEX_PATH)
    

if __name__ == "__main__":
    main()
