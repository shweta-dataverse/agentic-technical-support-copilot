from pathlib import Path
from copilot.ingestion.embedder import Embedder
from copilot.vectorstore.faiss_store import FAISSStore
from copilot.llm.model import OllamaLLM
from copilot.llm.chains import rag_chain

FAISS_PATH = Path("data/processed/faiss")
CHUNKS_PATH = Path("data/processed/chunks")

def main():
    # init embedder
    embedder = Embedder()
    dim = embedder.embed(["test"]).shape[1]

    # load faiss
    store = FAISSStore(dimension=dim)
    store.load(FAISS_PATH)

    # init llm
    llm = OllamaLLM(model_name="llama3.1")

    # real query
    question = "list all the accessories or spare parts of s7-1500?"

    answer = rag_chain(
        question=question,
        embedder=embedder,
        store=store,
        llm=llm,
        chunks_path=CHUNKS_PATH,
        k=5
    )

    print("\nfinal answer:\n")
    print(answer)
    print("\n")

if __name__ == "__main__":
    main()