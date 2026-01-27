# imports for evaluation using ragas 0.4.x
import pandas as pd
from ragas import evaluate
from datasets import Dataset, Features, Value
from ragas.metrics import ExactMatch, RougeScore, BleuScore, AnswerSimilarity
from copilot.utils.logger import get_logger
import numpy as np

logger = get_logger(__name__)

def evaluate_generation(queries, pred_key="predicted_answer", gold_key="actual_answer"):
    """
    evaluate generation metrics using ragas
    queries: list of dicts with predicted & expected answers
    returns aggregate + per-query metrics
    """

    # build dataset for ragas evaluation
    data = {
        "question": [str(q.get("question", "")).strip() for q in queries],  # questions
        "response": [str(q[pred_key]).strip() for q in queries],            # predicted answers
        "reference": [str(q[gold_key]).strip() for q in queries],           # actual answers
    }

    # define dataset schema
    features = Features({
        "question": Value("string"),
        "response": Value("string"),
        "reference": Value("string"),
    })

    # create ragas dataset
    dataset = Dataset.from_dict(data, features=features)
    print(f"\n\ndebug: dataset prepared for evaluation with {len(dataset)} rows\n\n")
    logger.info(f"\ndataset ready with {len(dataset)} tickets\n\n")

    # define metrics to evaluate
    metrics = [
        ExactMatch(),
        RougeScore(),
        BleuScore()
        #AnswerSimilarity()
    ]

    print("\n\ndebug: starting ragas evaluate\n\n")
    logger.info("\nexecuting ragas evaluation metrics\n\n")

    # evaluate dataset with ragas
    results = evaluate(
        dataset=dataset,
        metrics=metrics,
    )

    res_df = results.to_pandas()
    print("\n\ndebug: result columns: \n\n", res_df.columns.tolist(), "\n\n")
    logger.info("\nresults dataframe columns checked\n\n")

    # log per-query metrics
    for i, row in res_df.iterrows():
        logger.info(f"\nticket desc: {dataset[i]['question']}")
        logger.info(f"predicted: {dataset[i]['response']}")
        logger.info(f"actual: {dataset[i]['reference']}")
        logger.info(f"em: {row['exact_match']:.3f}")
        logger.info(f"rouge_l_fmeasure: {row['rouge_score(mode=fmeasure)']:.3f}")
        logger.info(f"bleu: {row['bleu_score']:.3f}")
        #logger.info(f"similarity: {row['answer_similarity']:.3f}")

    print("\n\ndebug: evaluation results processed\n\n")
    logger.info("\nfinished processing evaluation results\n\n")

    # return aggregate metrics + per-query metrics
    return {
        "em": float(np.mean(results["exact_match"])),
        "rouge_l": float(np.mean(results["rouge_score(mode=fmeasure)"])),
        "bleu": float(np.mean(results["bleu_score"])),
        #"similarity": float(np.mean(results["answer_similarity"])),
        "per_query": [
            {
                "question": dataset[i]["question"],
                "predicted": dataset[i]["response"],
                "actual": dataset[i]["reference"],
                "exact_match": row["exact_match"],
                "rouge_l_fmeasure": row["rouge_score(mode=fmeasure)"],
                "bleu": row["bleu_score"],
                #"similarity": row["answer_similarity"]
            }
            for i, row in res_df.iterrows()
        ],
    }