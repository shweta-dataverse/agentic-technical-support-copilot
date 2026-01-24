# prompt templates

def build_prompt(context: str, question: str) -> str:
    return f"""
you are an industrial automation support engineer.

answer the question using only the context below.
if the answer is not in the context, say "not found in manual".

context:
{context}

question:
{question}

answer:
"""