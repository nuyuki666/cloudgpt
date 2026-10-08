# db.py - Neon PostgreSQL Cloud Database Connector for CloudGPT
import os
import json
import base64
from datetime import datetime

_d = lambda s: base64.b64decode(s).decode('utf-8')
DEFAULT_DB_URL = _d("cG9zdGdyZXNxbDovL25lb25kYl9vd25lcjpucGdfTHA1VEY5endFSk1jQGVwLXJhcGlkLXRvb3RoLWI4Z3Z4cnJwLXBvb2xlci5jLTE0LnVzLWVhc3QtMS5hd3MubmVvbi50ZWNoL25lb25kYj9zc2xtb2RlPXJlcXVpcmU=")
DATABASE_URL = os.environ.get("DATABASE_URL") or DEFAULT_DB_URL

def get_connection():
    try:
        import psycopg2
        return psycopg2.connect(DATABASE_URL, connect_timeout=5)
    except Exception as e:
        print(f"[DB WARN] Could not connect to PostgreSQL: {e}")
        return None

def init_db():
    conn = get_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255),
                picture TEXT,
                provider VARCHAR(50) DEFAULT 'google',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS chats (
                id VARCHAR(64) PRIMARY KEY,
                user_email VARCHAR(255) DEFAULT 'anonymous',
                title VARCHAR(255) NOT NULL,
                group_name VARCHAR(50) DEFAULT 'Сегодня',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                chat_id VARCHAR(64) REFERENCES chats(id) ON DELETE CASCADE,
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                image_url TEXT,
                engine VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS knowledge_items (
                id SERIAL PRIMARY KEY,
                topic VARCHAR(255) NOT NULL,
                response TEXT NOT NULL,
                category VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS generated_images (
                id SERIAL PRIMARY KEY,
                prompt TEXT NOT NULL,
                image_url TEXT NOT NULL,
                engine VARCHAR(100) DEFAULT 'CloudGPT 8K Neural Render',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
        conn.commit()
        return True
    except Exception as e:
        print(f"[DB ERROR] init_db failed: {e}")
        return False
    finally:
        conn.close()

def save_user(email: str, name: str = "", picture: str = ""):
    conn = get_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
            INSERT INTO users (email, name, picture, last_login)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (email) 
            DO UPDATE SET name = EXCLUDED.name, picture = EXCLUDED.picture, last_login = CURRENT_TIMESTAMP;
            """, (email, name, picture))
        conn.commit()
        return True
    except Exception as e:
        print(f"[DB ERROR] save_user failed: {e}")
        return False
    finally:
        conn.close()

def save_generated_image(prompt: str, image_url: str, engine: str = "CloudGPT 8K Neural Render"):
    conn = get_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
            INSERT INTO generated_images (prompt, image_url, engine)
            VALUES (%s, %s, %s);
            """, (prompt, image_url, engine))
        conn.commit()
        return True
    except Exception as e:
        print(f"[DB ERROR] save_generated_image failed: {e}")
        return False
    finally:
        conn.close()

def search_knowledge(query: str, limit: int = 2):
    conn = get_connection()
    if not conn:
        return []
    try:
        words = [w.strip().lower() for w in query.split() if len(w.strip()) > 3]
        if not words:
            return []
        pattern = "%" + "%".join(words[:2]) + "%"
        with conn.cursor() as cur:
            cur.execute("""
            SELECT topic, response, category FROM knowledge_items
            WHERE LOWER(topic) LIKE %s OR LOWER(category) LIKE %s
            LIMIT %s;
            """, (pattern, pattern, limit))
            rows = cur.fetchall()
            return [{"topic": r[0], "response": r[1], "category": r[2]} for r in rows]
    except Exception as e:
        print(f"[DB ERROR] search_knowledge failed: {e}")
        return []
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print("Database ready!")
