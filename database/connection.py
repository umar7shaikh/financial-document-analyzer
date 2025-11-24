from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# ===== SQLAlchemy Setup (for table creation) =====
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

# Create SQLAlchemy engine and base
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===== psycopg2 Setup (for existing operations) =====
class DatabaseManager:
    def __init__(self):
        self.connection_params = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),  
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
    
    @contextmanager
    def get_db_connection(self):
        """Get database connection safely"""
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params, cursor_factory=RealDictCursor)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

# Create global instance
db_manager = DatabaseManager()
