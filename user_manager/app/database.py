import os
import time
import psycopg2

DB_HOST = os.getenv("DB_HOST", "user-db")
DB_NAME = os.getenv("DB_NAME", "user_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASSWORD", "password")

def get_db_connection():
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            return conn
        except Exception as e:
            print(f"[DB] Attesa connessione... ({retries} left) - {e}")
            time.sleep(2)
            retries -= 1
    return None

def init_db():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    email VARCHAR(255) PRIMARY KEY,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            print("[DB] Tabella users pronta.")
        except Exception as e:
            print(f"[DB] Errore init: {e}")
