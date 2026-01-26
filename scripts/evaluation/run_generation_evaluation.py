# scripts/run_generation_evaluation.py
from pathlib import Path
from copilot.ingestion.embedder import Embedder
from copilot.vectorstore.faiss_store import FAISSStore
from copilot.vectorstore.bm25_store import BM25Store
from copilot.vectorstore.hybrid_retriever import HybridRetriever
from copilot.llm.model import OllamaLLM
from copilot.llm.chains import rag_chain
from copilot.evaluation.generation_metrics import evaluate_generation
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

FAISS_PATH = Path("data/processed/faiss")
METADATA_PATH = Path("data/processed/faiss/metadata.pkl")  # bm25 metadata

def main():
    # initialize embedder
    logger.info("initializing embedder")
    embedder = Embedder()
    dim = embedder.embed(["test"]).shape[1]  # get embedding dimension

    # load faiss store
    logger.info("loading faiss store")
    faiss_store = FAISSStore(dimension=dim)
    faiss_store.load(FAISS_PATH)

    # load bm25 store
    logger.info("loading bm25 store")
    bm25_store = BM25Store.load_from_metadata(METADATA_PATH)

    # initialize llm
    logger.info("initializing llm")
    llm = OllamaLLM(model_name="llama3.1")

    # initialize hybrid retriever correctly (positional arguments)
    logger.info("initializing hybrid retriever")
    hybrid_retriever = HybridRetriever(
        faiss_store,   # first positional arg: vectorstore
        bm25_store,    # second positional arg: bm25 store
        embedder       # third positional arg: embedder
    )

    # wrapper function for rag_chain
    def rag_fn_wrapper(question):
        return rag_chain(
            question=question,
            hybrid_retriever=hybrid_retriever,
            llm=llm,
            k=5,
            alpha=0.5
        )

    # evaluation queries
    queries = [
        {
            "question": "overview of simatic s7-1500 automation system",
            "expected_answer": (
                "The SIMATIC S7-1500 automation system is designed for high performance, flexibility, "
                "and networking capability. It includes CPUs, distributed controllers (ET 200SP), "
                "PC-based controllers, and redundant systems (S7-1500R/H). Integrated motion control, "
                "fail-safe options, diagnostics, and security functions are provided (page 80 | chunk 101)."
            )
        },
        {
            "question": "comparison of simatic automation systems",
            "expected_answer": (
                "The SIMATIC S7-1200, ET 200SP, S7-1500, and S7-1500R/H systems differ in data work memory, "
                "code work memory, load memory, I/O address area, integrated interfaces, motion control functions, "
                "safety, and degree of protection. Advanced controllers and redundant systems offer higher memory "
                "and expanded functions (page 82 | chunk 105)."
            )
        },
        {
            "question": "installation requirements and mounting of s7-1500 system",
            "expected_answer": (
                "All S7-1500/ET 200MP modules are open equipment and must be installed indoors in secure housings or cabinets. "
                "Modules can be mounted horizontally (≤60°C) or vertically (≤40°C). Minimum clearances must be maintained, "
                "modules are connected with U connectors, and power must be off during installation. DIN rail adapters must be "
                "correctly clamped and fastened (5-6 Nm torque) (page 184 | chunk 202)."
            )
        },
        {
            "question": "safety symbols and warnings for s7-1500 devices",
            "expected_answer": (
                "Safety symbols indicate general warnings, electrical installation restrictions, device limitations, "
                "and compliance with EMC and ambient conditions. Devices without explosion protection must be installed by qualified personnel. "
                "Devices with explosion protection must follow low voltage, enclosure, and indoor-use requirements (page 22 | chunk 45)."
            )
        },
        {
            "question": "configuring cpu and hardware components in s7-1500",
            "expected_answer": (
                "Configuring involves arranging hardware in STEP 7, assigning parameters, and connecting modules. CPU addresses and hardware identifiers "
                "are automatically assigned. Configuration is downloaded to CPUs, and modules can be replaced without reconfiguring the system. "
                "STEP 7 ensures compatibility with CPU versions and article numbers (page 246 | chunk 512)."
            )
        }
    ]

    # run generation evaluation
    logger.info("running generation evaluation")
    metrics = evaluate_generation(rag_fn_wrapper, queries)

    # print results
    print("\n=== generation evaluation metrics ===")
    print("avg exact match:", metrics["avg_exact_match"])
    print("avg rouge-l score:", metrics["avg_rouge_l"])
    print("\nper query scores:")
    for q in metrics["per_query"]:
        print(f"question: {q['question']}")
        print(f"predicted: {q['predicted']}")
        print(f"expected: {q['expected']}")
        print(f"EM: {q['em']}, ROUGE-L: {q['rouge_l']:.3f}")
        print("-" * 60)

if __name__ == "__main__":
    main()