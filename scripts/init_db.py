import subprocess
import sys
from sqlalchemy import create_engine, text
import os
import logging
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_NAME = "rbi_compliance"
DB_USER = "postgres"
DB_PASS = "March2016@"
DB_HOST = "localhost"
DB_PORT = "5432"

def check_postgres_installation():
    """Check if PostgreSQL is installed and get its configuration"""
    try:
        # Try to get PostgreSQL installation info using pg_config
        result = subprocess.run(['pg_config', '--version'], 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            logger.info(f"Found PostgreSQL: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        logger.error("PostgreSQL is not installed or pg_config is not in PATH")
        return False

def create_database():
    """Create the database if it doesn't exist"""
    if not check_postgres_installation():
        raise Exception("PostgreSQL is not properly installed")

    try:
        # Connect to PostgreSQL server (not to a specific database)
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        exists = cursor.fetchone() is not None
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            logger.info(f"Created database {DB_NAME}")
        else:
            logger.info(f"Database {DB_NAME} already exists")
            
    except psycopg2.Error as e:
        logger.error(f"PostgreSQL Error: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

    # Test connection to the new database
    try:
        test_engine = create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
        with test_engine.connect() as conn:
            logger.info("Successfully connected to the new database")
    except Exception as e:
        logger.error(f"Error connecting to new database: {e}")
        raise

def init_migrations():
    """Initialize Alembic migrations"""
    try:
        # Create migrations directory if it doesn't exist
        migrations_dir = Path("migrations")
        if not migrations_dir.exists():
            os.system("alembic init migrations")
            logger.info("Initialized Alembic migrations")
            
            # Update alembic.ini with database URL
            with open("alembic.ini", "r") as f:
                content = f.read()
            
            content = content.replace(
                "sqlalchemy.url = driver://user:pass@localhost/dbname",
                f"sqlalchemy.url = postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            )
            
            with open("alembic.ini", "w") as f:
                f.write(content)
            
            logger.info("Updated alembic.ini with database URL")
            
            # Update env.py to import our models
            env_path = migrations_dir / "env.py"
            with open(env_path, "r") as f:
                content = f.read()
            
            import_str = """
from srcmodels.document_models import Base
target_metadata = Base.metadata
"""
            content = content.replace(
                "target_metadata = None",
                import_str
            )
            
            with open(env_path, "w") as f:
                f.write(content)
            
            logger.info("Updated migrations/env.py with models")
    
    except Exception as e:
        logger.error(f"Error initializing migrations: {e}")
        raise

def create_initial_migration():
    """Create and apply initial migration"""
    try:
        os.system('alembic revision --autogenerate -m "Initial migration"')
        logger.info("Created initial migration")
        
        os.system('alembic upgrade head')
        logger.info("Applied initial migration")
        
    except Exception as e:
        logger.error(f"Error creating/applying migration: {e}")
        raise

if __name__ == "__main__":
    create_database()
    init_migrations()
    create_initial_migration()
    logger.info("Database initialization complete")