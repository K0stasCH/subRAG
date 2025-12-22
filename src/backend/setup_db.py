import os
from dotenv import load_dotenv
import psycopg2


def get_db_string():
    load_dotenv()
    user = os.environ.get("POSTGRES_USER")
    pw = os.environ.get("POSTGRES_PASSWORD")
    host = os.environ.get("db_host")
    port = os.environ.get("POSTGRES_PORT")
    db = os.environ.get("POSTGRES_DB")
    return f"postgresql://{user}:{pw}@{host}:{port}/{db}"

def setup_db():
    with psycopg2.connect(get_db_string()) as conn:
        with conn.cursor() as cur:
            cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS movie_chunks (
                    id serial PRIMARY KEY,
                    content text,
                    embedding vector(384),
                    movie_name text)
            ''')
            conn.commit()