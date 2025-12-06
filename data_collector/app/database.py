import os
import time
import psycopg2

# Configurazione DB
DB_HOST = os.getenv("DB_HOST", "data-db")
DB_NAME = os.getenv("DB_NAME", "data_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASSWORD", "password")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        return conn
    except Exception as e:
        print(f"[DB] Errore connessione: {e}")
        return None

def init_db():
    time.sleep(5)  # aspetta avvio container Postgres

    conn = get_db_connection()
    if conn:
        cur = conn.cursor()

        # Tabella interessi utenti
        cur.execute("""
            CREATE TABLE IF NOT EXISTS interests (
                id SERIAL PRIMARY KEY,
                user_email VARCHAR(255) NOT NULL,
                airport_code VARCHAR(10) NOT NULL,
                UNIQUE(user_email, airport_code)
            );
        """)

        # Tabella voli
        cur.execute("""
            CREATE TABLE IF NOT EXISTS flights (
                id SERIAL PRIMARY KEY,
                airport_code VARCHAR(10),
                flight_json JSONB,
                obs_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("[DB] Tabelle pronte.")
