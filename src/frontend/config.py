from dotenv import load_dotenv
import os


load_dotenv()
API_BASE_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")