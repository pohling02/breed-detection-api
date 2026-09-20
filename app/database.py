import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Explicitly load the .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

# 2. Build the URL (Note the postgresql+psycopg:// prefix for SQLAlchemy)
DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:"
    f"{os.getenv('POSTGRES_PORT')}/"
    f"{os.getenv('POSTGRES_DB')}"
)

# 3. Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# 4. Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5. Define the Base class (This fixes the Alembic ImportError!)
Base = declarative_base()

# 6. Dependency to yield database sessions for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()