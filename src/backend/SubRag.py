from typing import List
import psycopg2, os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

from .config import *
from .dataSchemas import Query, Response
from .data_prep import initiate_data_prep, get_embeddings
from .setup_db import get_db_string, setup_db


class SubRag():
    def __init__(self):

        load_dotenv()
        if not os.environ.get("GEMINI_API_KEY"):
            raise Exception("❌ Error not API key found")
        
        self.history_store = {} # Stores history in memory
        self.embeddings = get_embeddings()
        self.db_connection = self._setup_db_connnection()
        self.movies = self._load_movies()
        self.rag_pipeline = self.load_rag_chain()
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
        try:
            setup_db()
            conn = psycopg2.connect(get_db_string())
            return conn
        except Exception as e:
            raise Exception(f"❌ Failed to connect to PGVector: {e}")
    

    def _load_movies(self) -> List[str]:
        def fetch_query():
            with self.db_connection.cursor() as cur:
                cur.execute('SELECT DISTINCT movie_name FROM movie_chunks ORDER BY movie_name;')
                return [row[0] for row in cur.fetchall()]

        movies = fetch_query()

        if not movies:
            initiate_data_prep()
            movies = fetch_query()
        
        print("ℹ️ Subtitles for movies loaded:", ", ".join(movies))
        
        return movies

    def _retrieve_relevant_chunks(self, my_query: str) -> List[dict]:
        query_embedding = self.embeddings.embed_query(my_query)
        with self.db_connection.cursor() as cur:
            cur.execute(
                """
                SELECT content, embedding <-> %s::vector as distance
                FROM movie_chunks
                ORDER BY distance
                LIMIT %s
                """,
                (query_embedding, self.number_of_retrieved_chunks),)

            results = [
                {"text": row[0], "distance": row[1]}
                for row in cur.fetchall()]

        return results

    def load_rag_chain(self):
        """Sets up the RAG logic using LCEL instead of a legacy chain."""
        llm = self._initialize_llm()
        
        # Define a custom prompt to control Gemini's behavior
        template = """
        You are a helpful assistant specialized in movie scripts.
        Answer the question based ONLY on the following context:
        {context}

        Question: {question}
        """
        prompt = ChatPromptTemplate.from_template(template)

        # Create the retriever bridge
        retriever = PostgresRetriever(rag_instance=self)

        # Create the LCEL Chain
        # This pipes: Context/Question -> Prompt -> LLM -> String Output
        rag_pipeline = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        print("✅ LCEL RAG Pipeline initialized.")
        return rag_pipeline
    
    def rag_response(self, query: str, session_id: str) -> Response:
        """
        Executes the RAG pipeline and returns a structured Response.
        """
        try:
            answer = self.rag_pipeline.invoke(query)
        except Exception as e:
            answer = f"\n❌ ERROR during RAG execution: {e}\n"
        finally:
            return Response(query=query, answer=answer)
    
    def delete_history_with(self, session_id: str):
        print(f"delete {session_id}")
    
class PostgresRetriever(BaseRetriever):
    rag_instance: any 

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        # Reuse your existing manual SQL retrieval method
        from .dataSchemas import Query
        results = self.rag_instance._retrieve_relevant_chunks(query)
        
        # Convert your dict results into LangChain Document objects
        return [Document(page_content=r["text"]) for r in results]

if __name__ == '__main__':
    
    rag = SubRag()
    test_query = "What did the main character say about their family?"
    result = rag.rag_response(test_query)

    print("\n" + "="*50)
    print(f"TEST QUERY: {test_query}")
    print(f"ANSWER:\n{result['result']}")
    print("="*50)