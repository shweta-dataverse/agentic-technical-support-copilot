# retrieval augmented generation chain using hybrid retriever

from copilot.vectorstore.hybrid_retriever import HybridRetriever
from copilot.llm.prompts import build_prompt
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

def rag_chain(
    question: str,
    hybrid_retriever: HybridRetriever,
    llm,
    k: int = 5,
    alpha: float = 0.5
) -> str:
    """
    generate answer using hybrid retrieval + llm
    """

    try:
        logger.info("starting rag pipeline")

        # retrieve top-k chunks using hybrid retriever
        logger.info("retrieving relevant chunks")
        retrieved_chunks = hybrid_retriever.retrieve(question, k=k, alpha=alpha)

        # combine retrieved chunks into context
        context = "\n\n".join(
            [f"page {c['page']} | chunk {c['chunk_id']}\n{c['text']['text']}" 
             for c in retrieved_chunks]
        )

        # build prompt with question + context
        logger.info("building prompt")
        prompt = build_prompt(context, question)

        # generate answer from llm
        logger.info("generating answer from llm")
        answer = llm.generate(prompt)

        logger.info("rag pipeline completed")
        return answer

    except Exception:
        logger.error("rag pipeline failed", exc_info=True)
        raise