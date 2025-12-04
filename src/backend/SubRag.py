# Components for Retrieval (R)
from langchain_community.vectorstores import FAISS
# Components for Generation (G)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains import RetrievalQA

from .config import *
from .data_prep import create_and_save_or_load_embeddings

from dotenv import load_dotenv
import os

class SubRag():
    def __init__(self):
        load_dotenv()
        if not os.environ.get("GEMINI_API_KEY"):
            raise Exception("❌ Error not API key found")
        
        self.vector_store = create_and_save_or_load_embeddings()
        self.qa_chain = self.load_rag_chain()

    def _initialize_llm(self):
        print(f"Initializing Gemini LLM with model: {GEMINI_MODEL_NAME}")
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL_NAME,
            temperature=TEMPERATURE
        )
        return llm

    def load_rag_chain(self) -> RetrievalQA:
        """
        Initializes the Gemini LLM and creates the LangChain RetrievalQA chain.
        """
        # 1. Initialize the Local LLM (The "G" component)
        llm = self._initialize_llm()
        print("✅ Local LLM initialized.")

        # 2. Create the Retriever (The "R" component)
        retriever = self.vector_store.as_retriever(search_kwargs=SEARCH_KWARGS)
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

    def rag_response(self, query: str):
        result = None # Initialize result
        try:
            result = self.qa_chain.invoke({"query": query})
        except Exception as e:
            print(f"\n❌ ERROR during RAG execution: {e}\n")
            # Return an error object or dictionary instead of an undefined result
            return {"query": query, "result": "An error occurred during generation.", "source_documents": []}
        return result

if __name__ == '__main__':
    
    rag = SubRag()
    test_query = "What did the main character say about their family?"
    result = rag.rag_response(test_query)

    print("\n" + "="*50)
    print(f"TEST QUERY: {test_query}")
    print(f"ANSWER:\n{result['result']}")
    print("="*50)