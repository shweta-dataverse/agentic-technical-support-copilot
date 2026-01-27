# scripts/init_db.py

from copilot.db.connection import engine
from copilot.db.models import Base

def main():
    Base.metadata.create_all(bind=engine)
    print("tables created")

if __name__ == "__main__":
    main()