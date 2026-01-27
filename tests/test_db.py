# scripts/test_db.py

from copilot.db.connection import engine

def main():
    try:
        conn = engine.connect()
        print("db connection successful")
        conn.close()
    except Exception as e:
        print("db connection failed")
        print(e)

if __name__ == "__main__":
    main()