"""
Database connection management for SQL Server.
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_connection_string() -> str:
    """
    Build SQL Server connection string from environment variables.
    
    Returns:
        Connection string for SQLAlchemy
    """
    server = os.getenv("DB_SERVER", "localhost")
    database = os.getenv("DB_NAME", "StockCryptoDB")
    driver = "ODBC+Driver+17+for+SQL+Server"
    
    conn_str = f"mssql+pyodbc://{server}/{database}?driver={driver}"
    return conn_str


def get_engine():
    """
    Create and return SQLAlchemy engine.
    
    Returns:
        SQLAlchemy Engine object
    """
    conn_str = get_connection_string()
    engine = create_engine(
        conn_str,
        echo=False,  # Set True for SQL debugging
        pool_pre_ping=True  # Verify connections before using
    )
    return engine


def get_session():
    """
    Create and return SQLAlchemy session for ORM operations.
    
    Returns:
        SQLAlchemy Session object
    """
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def test_connection():
    """
    Test database connection.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database connection successful!")
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test the connection when run directly
    test_connection()
