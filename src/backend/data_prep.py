from langchain_community.document_loaders import SRTLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from typing import List
import re
from .config import *
import psycopg2
from dotenv import load_dotenv
from .setup_db import get_db_string, setup_db
from pathlib import Path

load_dotenv()







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

def split_text(documents: List[str], chunk_size: int = 1000, chunk_overlap: int = 200):
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
    print(f"✅ Successfully loaded local embedding model: {model_name}")
    return embeddings

def store_in_db(split_chunks, embeddings_model, movie_name:str):
    setup_db()

    with psycopg2.connect(get_db_string()) as conn:
        with conn.cursor() as cur:
            if movie_exists(movie_name):
                print(f"ℹ️ The movie '{movie_name}' already exists in the database.")
                return
            else:
                print(f"ℹ️ The movie '{movie_name}' don't exists in the database.")

            # 3. Insert chunks
            print(f"ℹ️ Storing {len(split_chunks)} chunks in Postgres...")
            embeddings = get_embeddings(embeddings_model)
            for doc in split_chunks:
                # Generate the embedding vector
                vector = embeddings.embed_query(doc.page_content)
                
                cur.execute(
                    "INSERT INTO movie_chunks (content, embedding, movie_name) VALUES (%s, %s, %s)",
                    (doc.page_content, vector, movie_name)
                )
            
            conn.commit()
        print("✅ All vectors stored successfully!")

def movie_exists(movie_name):
    # Use 'with' for both connection and cursor to ensure they close properly
    with psycopg2.connect(dsn=get_db_string()) as conn:
        with conn.cursor() as cur:
            # 2. Add a comma after movie_name to make it a tuple
            cur.execute(
                "SELECT EXISTS(SELECT 1 FROM movie_chunks WHERE LOWER(movie_name) = LOWER(%s) LIMIT 1)", 
                (movie_name,)
            )

            res = cur.fetchone()
            return res[0] if res else False

def initiate_data_prep():
    for movie_path in SRT_PATHS:
        loader = SRTLoader(movie_path)
        docs = loader.load()
        for doc in docs:
            doc.page_content = clean_subtitle_text(doc.page_content)
        split_chunks = split_text(docs, CHUNK_SIZE, CHUNK_OVERLAP)
        store_in_db(split_chunks, HF_EMBEDDING_MODEL, Path(SRT_PATHS[0]).stem)