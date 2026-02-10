# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL connection string (required)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   
    future=True           
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# # app/database.py
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base
# import os
# from dotenv import load_dotenv

# load_dotenv()

# # Use environment variable or default for local SQLite (easier for testing)
# DATABASE_URL = os.getenv(
#     "DATABASE_URL",
#     "sqlite:///./rbac.db"
# )

# if DATABASE_URL.startswith("sqlite"):
#     engine = create_engine(
#         DATABASE_URL,
#         connect_args={"check_same_thread": False}
#     )
# else:
#     engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# SessionLocal = sessionmaker(
# autocommit=False,
# autoflush=False,
# bind=engine)

# Base = declarative_base()

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

