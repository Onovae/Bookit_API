import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

load_dotenv()

def recreate_database():
    database_url = os.getenv('DATABASE_URL')
    result = urlparse(database_url)
    
    # Connect to PostgreSQL server (not to the specific database)
    conn = psycopg2.connect(
        host=result.hostname,
        port=result.port or 5432,
        user=result.username,
        password=result.password,
        database='postgres'  # Connect to default postgres database
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    cursor = conn.cursor()
    
    # Drop existing database - force disconnect sessions
    print("Dropping database...")
    cursor.execute(f"""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '{result.path[1:]}' AND pid <> pg_backend_pid()
    """)
    cursor.execute(f"DROP DATABASE IF EXISTS {result.path[1:]}")
    
    # Create new database
    print("Creating database...")
    cursor.execute(f"CREATE DATABASE {result.path[1:]}")
    
    cursor.close()
    conn.close()
    
    print("✅ Database recreated successfully!")

if __name__ == "__main__":
    recreate_database()