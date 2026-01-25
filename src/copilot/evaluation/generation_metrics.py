# copilot/evaluation/generation_metrics.py
from rouge_score import rouge_scorer
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

def exact_match(predicted, expected):
    """check if predicted answer exactly matches expected"""
    return int(predicted.strip().lower() == expected.strip().lower())

def rouge_l_score(predicted, expected):
    """compute rouge-l fmeasure for text overlap"""
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    score = scorer.score(expected, predicted)
    return score["rougeL"].fmeasure

def evaluate_generation(rag_fn, queries):
    """
    evaluates LLM answers using EM and ROUGE-L
    rag_fn: function that takes question and returns answer
    queries: list of dicts {"question": str, "expected_answer": str}
    """
    em_scores = []
    rouge_scores = []

    for q in queries:
        question = q["question"]
        expected_answer = q["expected_answer"]

        # generate answer
        predicted_answer = rag_fn(question)
        logger.info(f"question: {question}")
        logger.info(f"predicted: {predicted_answer}")
        logger.info(f"expected: {expected_answer}")

        em_scores.append(exact_match(predicted_answer, expected_answer))
        rouge_scores.append(rouge_l_score(predicted_answer, expected_answer))

    # log averages
    avg_em = sum(em_scores) / len(em_scores)
    avg_rouge = sum(rouge_scores) / len(rouge_scores)
    logger.info(f"average EM: {avg_em:.3f}, average ROUGE-L: {avg_rouge:.3f}")

    return {
        "avg_exact_match": avg_em,
        "avg_rouge_l": avg_rouge,
        "per_query": [{"question": q["question"],
                       "predicted": rag_fn(q["question"]),
                       "expected": q["expected_answer"],
                       "em": em_scores[i],
                       "rouge_l": rouge_scores[i]}
                      for i, q in enumerate(queries)]
    }