# retrieval augmented generation chain

from copilot.vectorstore.retriever import retrieve
from copilot.llm.prompts import build_prompt
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

def rag_chain(
    question: str,
    embedder,
    store,
    chunks_path,
    llm,
    k: int = 5
) -> str:
    try:
        logger.info("starting rag pipeline\n")

        # embed question
        logger.info("embedding user question\n")
        query_embedding = embedder.embed([question])[0]

        # retrieve context
        logger.info("retrieving relevant chunks\n")
        chunks = retrieve(
            query_embedding=query_embedding,
            store=store,
            k=k
        )

        context = "\n\n".join(
            [f"page {chunk['page']}\n{chunk['text']}" for chunk in chunks]
        )

        # build prompt
        logger.info("building prompt\n")
        prompt = build_prompt(context, question)

        # generate answer
        logger.info("generating answer from llm\n")
        answer = llm.generate(prompt)

        logger.info("rag pipeline completed\n")
        return answer

    except Exception:
        logger.error("rag pipeline failed\n", exc_info=True)
        raise