# src/copilot/llm/answer_generator.py

from copilot.llm.prompts import RAG_GROUNDED_PROMPT
from copilot.llm.model import OllamaModel
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

class AnswerGenerator:
    def __init__(self, model_name: str = "llama3"):
        self.llm = OllamaModel(model_name=model_name)

    def build_context(self, retrieved_chunks: list) -> str:
        """
        Combine retrieved chunks into a single context string.
        """
        context_blocks = []

        for chunk in retrieved_chunks:
            block = (
                f"[page {chunk['page']} | chunk {chunk['chunk_id']}]\n"
                f"{chunk['text']}"
            )
            context_blocks.append(block)

        return "\n\n".join(context_blocks)

    def generate_answer(self, question: str, retrieved_chunks: list) -> str:
        try:
            logger.info("Generating grounded answer")

            context = self.build_context(retrieved_chunks)

            prompt = RAG_GROUNDED_PROMPT.format(
                context=context,
                question=question
            )

            response = self.llm.generate(prompt)

            return response

        except Exception:
            logger.error("Answer generation failed", exc_info=True)
            raise