from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .dataSchemas import Query, Health_Status
from .SubRag import SubRag
from contextlib import asynccontextmanager
import os
import sys


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initializes the RAG instance and stores it in app.state for dependency access.
    Handles cleanup when the application shuts down.
    """
    # 1. Initialization
    try:
        print("Attempting to initialize RAG instance...")
        # Check for required environment variables early
        if not os.getenv("GEMINI_API_KEY"):
            # Use sys.exit or similar for a hard failure if a critical resource is missing
            print("❌ Error not API key found")
            sys.exit(1)
            
        # The SubRag constructor handles FAISS loading and chain setup
        # Store the initialized instance directly on the app's state object
        app.state.rag_instance = SubRag() 
        print("✅ RAG Instance initialized successfully and stored in app.state.")
    except Exception as e:
        print(f"❌ Critical Error initializing the RAG instance.\nError: {e}")
        # Set a clear state failure flag
        app.state.rag_instance = None
    
    # 2. Yield (Start serving requests)
    yield

    # 3. Cleanup
    print("Application shutting down...")
    # Access the instance from app.state for cleanup
    if hasattr(app.state, 'rag_instance') and app.state.rag_instance:
        # Add any necessary cleanup logic here if SubRag requires it (e.g., closing connections)
        # if hasattr(app.state.rag_instance, 'cleanup'):
        #     await app.state.rag_instance.cleanup()
        app.state.rag_instance = None
        print("RAG Instance cleaned up.")


# Load environment variables (including GEMINI_API_KEY)
load_dotenv()

# --- App Initialization ---
# Pass the lifespan function to the FastAPI constructor
app = FastAPI(lifespan=lifespan)


# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    # IMPORTANT: Use a list of specific origins in production for security!
    # e.g., allow_origins=["https://yourfrontend.com", "http://localhost:3000"]
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API Endpoints ---
@app.get("/api/status")
async def get_health_status():
    """Default route to check API health."""
    # Check the state of the RAG instance for a more accurate health check
    status = "online" if hasattr(app.state, 'rag_instance') and app.state.rag_instance else "degraded (RAG not initialized)"
    return Health_Status(message="RAG API is running!", status=status)

@app.delete("/delete_History/{uuid}")
async def delete_History(uuid: str):
    app.state.rag_instance.delete_history_with(uuid)

@app.post("/api/query")
async def process_query(query_data: Query):
    """
    Endpoint to receive a user query and process it through the RAG chain.
    """
    # 1. Access RAG Instance via app.state
    rag_instance = app.state.rag_instance if hasattr(app.state, 'rag_instance') else None
    
    if rag_instance is None:
        raise HTTPException(
            status_code=503, 
            detail="❌ RAG service is not initialized. Check server logs for initialization errors."
        )
        
    user_query = query_data.query # Access the query string from the Pydantic model
    user_session_id = query_data.session_id
    
    try:
        # Get the response from the RAG system
        # Ensure rag_response is either synchronous or properly awaited if it's async
        # We assume it is synchronous based on your original code: rag_instance.rag_response(user_query)
        result = rag_instance.rag_response(user_query, user_session_id)

        # Structure the response for the frontend
        response_data = {
            "query": result.query,
            "answer": result.answer,
        }
        
        return response_data

    except Exception as e:
        # Catch any remaining runtime errors during RAG processing
        print(f"❌ Error processing RAG query: {e}")
        # Log the full traceback for better debugging
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500, 
            detail=f"❌ Internal server error during RAG processing. Details: {type(e).__name__}"
        )