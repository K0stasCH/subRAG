from typing import List, Optional
from langchain_core.documents import Document

# Components for Retrieval (R)
from langchain_community.vectorstores import FAISS

# Components for Generation (G)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains import RetrievalQA


from config import *
from data_prep import create_and_save_or_load_embeddings

import os
from dotenv import load_dotenv



def load_rag_chain(vector_store: FAISS) -> RetrievalQA:
    """
    Sets up the local Ollama LLM and creates the RetrievalQA chain.
    """
    # 1. Initialize the Local LLM (The "G" component)
    print(f"Initializing Gemini LLM with model: {GEMINI_MODEL_NAME}")
    # Note: Ensure your Ollama server is running (ollama serve)
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL_NAME,
        temperature=TEMPERATURE
    )

    # 2. Create the Retriever (The "R" component)
    retriever = vector_store.as_retriever(search_kwargs=SEARCH_KWARGS)
    print(f"Retriever set up to fetch top {SEARCH_KWARGS['k']} chunks.")

    # 3. Create the RetrievalQA Chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff", # 'stuff' means all retrieved docs are 'stuffed' into the prompt
        retriever=retriever,
        return_source_documents=True # Important for checking RAG performance
    )
    print("✅ RetrievalQA Chain fully initialized.")
    return qa_chain

if __name__ == '__main__':
    
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    # This block allows you to test the file independently
    try:
        # Test loading the index (must have run main.py first to create it)
        vector_store = create_and_save_or_load_embeddings()
        qa_chain = load_rag_chain(vector_store)

        # Example query
        test_query = "What did the main character say about their family?"
        result = qa_chain.invoke({"query": test_query})
        
        print("\n" + "="*50)
        print(f"TEST QUERY: {test_query}")
        print(f"ANSWER:\n{result['result']}")
        print("="*50)

    except Exception as e:
        print(f"\n--- ERROR during test execution: {e} ---")
        print("Please ensure your Ollama server is running and the FAISS index has been created.")