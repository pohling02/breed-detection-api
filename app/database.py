import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Load .env file without overwriting explicit test/CI environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)

# 2. Build the URL (allow TEST_DATABASE_URL override for local WSL pytest)
DATABASE_URL = os.getenv("TEST_DATABASE_URL") or (
    f"postgresql+psycopg://"
    f"{os.getenv('POSTGRES_USER', 'test')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'test')}@"
    f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB', 'testdb')}"
)

# 3. Create the SQLAlchemy engine
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# 4. Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5. Define the Base class
Base = declarative_base()

# 6. Dependency to yield database sessions for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
