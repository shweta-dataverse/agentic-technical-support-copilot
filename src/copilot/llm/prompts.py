RAG_GROUNDED_PROMPT = """
You are a technical documentation assistant.

Answer the user's question using ONLY the provided context.
Do NOT use any external knowledge.
If the answer is not present in the context, say:
"I could not find the answer in the provided documentation."

Rules:
- Be concise and technical
- Cite sources at the end
- Each citation must follow this format: page X | chunk Y

Context:
{context}

Question:
{question}

Answer:
"""

def build_prompt(context: str, question: str) -> str:
    """
    Fill the RAG prompt template with context and question
    """
    return RAG_GROUNDED_PROMPT.format(context=context, question=question)