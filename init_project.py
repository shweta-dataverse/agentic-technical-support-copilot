import os
from pathlib import Path

# defining the directories and files for the copilot project
# this structure follows senior-level python package conventions
project_root = "."

# directory list
directories = [
    "data/raw/manuals",
    "data/processed/chunks",
    "notebooks",
    "src/copilot/ingestion",
    "src/copilot/vectorstore",
    "src/copilot/llm",
    "src/copilot/agents",
    "src/copilot/workflows",
    "src/copilot/evaluation",
    "scripts",
    "tests"
]

# file list
files = [
    ".env.example",
    "src/copilot/__init__.py",
    "src/copilot/ingestion/__init__.py",
    "src/copilot/ingestion/pdf_loader.py",
    "src/copilot/ingestion/text_splitter.py",
    "src/copilot/ingestion/embedder.py",
    "src/copilot/vectorstore/__init__.py",
    "src/copilot/vectorstore/faiss_store.py",
    "src/copilot/vectorstore/retriever.py",
    "src/copilot/llm/__init__.py",
    "src/copilot/llm/prompts.py",
    "src/copilot/llm/model.py",
    "src/copilot/llm/chains.py",
    "src/copilot/agents/__init__.py",
    "src/copilot/agents/knowledge_agent.py",
    "src/copilot/agents/jira_agent.py",
    "src/copilot/agents/synthesis_agent.py",
    "src/copilot/workflows/__init__.py",
    "src/copilot/workflows/langgraph_flow.py",
    "src/copilot/evaluation/__init__.py",
    "src/copilot/evaluation/rag_metrics.py",
    "src/copilot/app.py",
    "scripts/ingest_docs.py",
    "scripts/run_copilot.py",
    "tests/test_retrieval.py"
]

def build_project():
    print("\n[debug] starting professional folder construction...\n")
    
    # creating directories
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        # adding .gitkeep to ensure empty data folders are tracked
        if "data" in directory or "notebooks" in directory:
            (path / ".gitkeep").touch()
            print(f"[debug] directory created with .gitkeep: {directory}\n")
        else:
            print(f"[debug] directory created: {directory}\n")

    # creating empty files
    for file_path in files:
        path = Path(file_path)
        if not path.exists():
            path.touch()
            print(f"[debug] file initialized: {file_path}\n")
        else:
            print(f"[debug] file already exists, skipping: {file_path}\n")

    print("[debug] project structure successfully built. time to code.\n")

if __name__ == "__main__":
    build_project()