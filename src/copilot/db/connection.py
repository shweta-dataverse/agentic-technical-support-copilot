# src/copilot/db/connection.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# db connection url
# format: postgresql://user:password@host:port/dbname
DATABASE_URL = "postgresql://shwetabambal@localhost:5432/jira_copilot"

# create engine
engine = create_engine(DATABASE_URL, echo=False)

# session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# dependency to get db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()