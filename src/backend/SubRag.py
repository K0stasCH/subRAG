# Components for Retrieval (R)
# from langchain_community.vectorstores import PGVector
# Components for Generation (G)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains import RetrievalQA

from .data_prep import get_embeddings

from .config import *
import psycopg2
from dotenv import load_dotenv
import os
from .dataSchemas import Query
from .data_prep import main

class SubRag():
    def __init__(self):
        print(",.................")
        main()
        print(",.................")
        load_dotenv()
        if not os.environ.get("GEMINI_API_KEY"):
            raise Exception("❌ Error not API key found")
        
        self.embeddings = get_embeddings()
        self.db_connection = self._setup_db_connnection()
        self.qa_chain = self.load_rag_chain()
        self.number_of_retrieved_chunks = SEARCH_KWARGS['k']


    def _initialize_llm(self):
        print(f"Initializing Gemini LLM with model: {GEMINI_MODEL_NAME}")
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL_NAME,
            temperature=TEMPERATURE
        )
        return llm
    
    def _setup_db_connnection(self):
        """
        Connects to PostgreSQL using pgvector.
        This does NOT load vectors into memory. It creates a connection object.
        """

        COLLECTION_NAME = POSTGRES_COLLECTION_NAME
        
        try:
            print(f"Connecting to PGVector database: {COLLECTION_NAME}...")
            
            # This object acts as the interface to the DB. 
            # It runs SQL queries for retrieval.
            conn = psycopg2.connect(
                dbname=os.environ.get("POSTGRES_DB"),
                user=os.environ.get("POSTGRES_USER"),
                password=os.environ.get("POSTGRES_PASSWORD"),
                host=os.environ.get("db_host"),  #is published throught docker compose
                port=os.environ.get("POSTGRES_PORT"),
            )
            print("✅ Database connection established.")
            return conn
        except Exception as e:
            raise Exception(f"❌ Failed to connect to PGVector: {e}")

    def _retrieve_relevant_chunks(self, query: Query):
        query_embedding = self.embeddings.embed_query(query)

        conn = self._setup_db_connnection()
        cur = conn.cursor()

        # cur.execute(
        #     """
        #     SELECT chunk_text, metadata, embedding <-> %s::vector as distance
        #     FROM document_chunks
        #     ORDER BY distance
        #     LIMIT %s
        # """,
        #     (query_embedding, k),
        # )

        # results = [
        #     {"text": row[0], "metadata": row[1], "distance": row[2]}
        #     for row in cur.fetchall()
        # ]
        results = None
        cur.close()
        conn.close()
        return results

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