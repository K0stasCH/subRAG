import os
import psycopg2
from dotenv import load_dotenv


def connect_to_db():
    load_dotenv()
    return psycopg2.connect(
        dbname=os.environ.get("POSTGRES_DB"),
        user=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD"),
        host=os.environ.get("db_host"),  #is published throught docker compose
        port=os.environ.get("POSTGRES_PORT"),
    )