from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from ..backend.SubRag import SubRag
from .dataSchemas import Query



# --- App Initialization ---
app = FastAPI()

# Load environment variables (including GEMINI_API_KEY)
load_dotenv()

# --- CORS Configuration ---
# Allows the frontend (running on a different port/domain) to connect to the backend.
# IMPORTANT: Adjust 'allow_origins' in a production environment for security.
app.add_middleware(
    CORSMiddleware,
    # For local development, allow all origins
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- RAG Initialization ---
rag_instance = None

@app.on_event("startup")
def startup_event():
    """Initializes the RAG instance when the FastAPI server starts."""
    global rag_instance
    try:
        print("Attempting to initialize RAG instance...")
        # The SubRag constructor will handle FAISS loading and chain setup
        rag_instance = SubRag()
        print("✅ RAG Instance initialized successfully.")
    except Exception as e:
        print(f"❌ Critical Error initializing the RAG instance.\nError: {e}")
        # Optionally raise HTTPException here to prevent server startup, but for now, we'll log and continue.
        # If rag_instance is None, the RAG endpoint will handle the error.
        

# --- API Endpoints ---
@app.get("/")
def read_root():
    """Default route to check API health."""
    return {"message": "RAG API is running!", "status": "online"}

@app.post("/api/query")
async def process_query(data: dict):
    """
    Endpoint to receive a user query and process it through the RAG chain.
    The frontend sends JSON data: {"query": "The user's question..."}
    """
    if rag_instance is None:
        raise HTTPException(status_code=503, detail="RAG service is not initialized. Check server logs for errors.")
        
    user_query = data["query"]
    if not user_query:
        raise HTTPException(status_code=400, detail="Missing 'query' parameter in request body.")

    try:
        # Get the response from the RAG system
        result = rag_instance.rag_response(user_query)

        # Structure the response for the frontend
        response_data = {
            "query": result.get("query"),
            "answer": result.get("result"),
            "sources": [
                {
                    "content": doc.page_content,
                    # Assuming metadata has a 'source' field (e.g., filename)
                    "source_id": doc.metadata.get('source', 'N/A'), 
                    "metadata": doc.metadata # Include all metadata if needed
                }
                for doc in result.get("source_documents", [])
            ]
        }
        
        return response_data

    except Exception as e:
        # Catch any remaining runtime errors during RAG processing
        print(f"Error processing RAG query: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error during RAG processing: {e}")