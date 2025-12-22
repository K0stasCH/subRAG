# --- FILE PATHS ---
# Paths are relative to the project root
SRT_PATHS = ["subtitles/raw/Terminator.3.srt"]
CLEANED_TEXT_PATH = "data/processed/cleaned_dialogue.txt"
FAISS_INDEX_PATH = "index/movie_script_faiss_index"

DEVICE = "cpu"

# --- CHUNKING PARAMETERS ---
CHUNK_SIZE = 1000    # Max characters per text chunk
CHUNK_OVERLAP = 200 # Overlap between adjacent chunks

# --- EMBEDDING PARAMETERS ---
# Model used for generating vector embeddings (runs locally)
HF_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
 
# --- LLM/RAG PARAMETERS ---
GEMINI_MODEL_NAME = "gemini-2.5-flash"
SEARCH_KWARGS = {"k": 4} # Number of chunks to retrieve for each query
TEMPERATURE = 0.0   # LLM creativity (0.0 is deterministic/factual)
