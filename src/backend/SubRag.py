from typing import List
import psycopg2, os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

from .config import *
from .dataSchemas import Response
from .data_prep import initiate_data_prep, get_embeddings
from .setup_db import get_db_string, setup_db


class SubRag():
    def __init__(self):

        load_dotenv()
        if not os.environ.get("GEMINI_API_KEY"):
            raise Exception("❌ Error not API key found")
        
        self.history_store = {} # Stores history in memory
        self.embeddings = get_embeddings()
        self.llm = self._initialize_llm()
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
        llm = self.llm
        
        # --- STEP 1: Define the Re-phrase Prompt ---
        rephrase_template = """
        You are an AI assistant tasked with reformulating user queries. 
        Given a conversation history and a follow-up question, 
        your goal is to rephrase the follow-up question into a standalone question 
        that contains all necessary context.

        Instructions:
        1. Do not answer the question.
        2. Maintain the original intent and meaning.
        3. If the question is already standalone, return it exactly as is.
        4. Remove all pronouns (e.g., "it", "they", "that") and replace them with the specific subjects from the history.
        5. Output only the rephrased question.
        """
        rephrase_prompt = ChatPromptTemplate.from_messages([
            ("system", rephrase_template),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{initial_question}"),
        ])
        
        # This sub-chain creates the standalone query string
        rephrase_chain = rephrase_prompt | llm | StrOutputParser()
        
        # --- STEP 2: Define the Final RAG Prompt ---
        template = """
        You are a helpful assistant specialized in movie scripts.
        If the answer isn't in the context, say you don't know based on the script.
        Answer the question based ONLY on the following context:
        {final_context}
        """
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", template),
            ("human", "{rephrased_question}"),
        ])

        retriever = PostgresRetriever(rag_instance=self)

        # --- STEP 3: The Combined Pipeline ---
        def get_context_and_question(input_dict):
            # We re-phrase the question first using history
            standalone_question = rephrase_chain.invoke({
                "chat_history": input_dict["chat_history"],
                "initial_question": input_dict["init_question"]
            })
            print(f"ℹ️: Re-phrased question: {standalone_question}")
            # Then retrieve using the standalone version
            return {
                "final_context": retriever.invoke(standalone_question),
                "rephrased_question": standalone_question,
            }

        self.rag_pipeline = (
            get_context_and_question 
            | qa_prompt 
            | llm 
            | StrOutputParser()
        )
        return self.rag_pipeline
    
    def rag_response(self, query: str, session_id: str) -> Response:
        with_history = RunnableWithMessageHistory(
            self.rag_pipeline,
            self._get_session_history,
            input_messages_key="init_question",
            history_messages_key="chat_history",
        )
        
        try:
            # We pass a config object with the session_id
            answer = with_history.invoke(
                {"init_question": query},
                config={"configurable": {"session_id": session_id}}
            )
        except Exception as e:
            answer = f"\n❌ ERROR during RAG execution: {e}\n"
        
        return Response(query=query, answer=answer)
    
    def _delete_history_with(self, session_id: str):
        self.history_store.pop(session_id, None)
    
    def _get_session_history(self, session_id: str):
        if session_id not in self.history_store:
            self.history_store[session_id] = ChatMessageHistory()
        return self.history_store[session_id]
    
class PostgresRetriever(BaseRetriever):
    rag_instance: any 

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        # Reuse your existing manual SQL retrieval method
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