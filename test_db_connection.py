import os
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

def test_db_connection():
    try:
        database_url = os.getenv('DATABASE_URL')
        print(f"Testing connection to: {database_url}")
        
        # Parse the URL
        result = urlparse(database_url)
        
        # Connect to PostgreSQL
        connection = psycopg2.connect(
            host=result.hostname,
            port=result.port or 5432,
            database=result.path[1:],  # Remove leading slash
            user=result.username,
            password=result.password
        )
        
        # Test the connection
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Database connection successful!")
        print(f"PostgreSQL version: {version[0]}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    test_db_connection()