# updated imports for ragas 0.4.x compatibility
import pandas as pd
from ragas import evaluate
from datasets import Dataset, Features, Value, Sequence
from ragas.metrics import ExactMatch, RougeScore, BleuScore
from copilot.utils.logger import get_logger
import numpy as np

logger = get_logger(__name__)


def _safe_text(x):
    # ensure no nan / none reaches ragas
    if x is None:
        return ""
    if isinstance(x, float) and pd.isna(x):
        return ""
    return str(x).strip()


def evaluate_generation(queries, pred_key="predicted_answer", gold_key="expected_answer"):
    """
    evaluate generation metrics using ragas
    queries: list of dicts with predicted & expected answers
    returns aggregate + per-query metrics
    """

    # build clean dataset
    data = {
        "question": [_safe_text(q.get("question", "")) for q in queries],
        "answer": [_safe_text(q[pred_key]) for q in queries],
        "reference": [[_safe_text(q[gold_key])] for q in queries],
    }

    # explicit schema to avoid pyarrow bugs
    features = Features({
        "question": Value("string"),
        "answer": Value("string"),
        "reference": Value("string"),
    })

    dataset = Dataset.from_dict(data, features=features)

    print(f"debug: dataset prepared for evaluation with {len(dataset)} rows\n")

    metrics = [
        ExactMatch(),
        RougeScore(),
        BleuScore(),
    ]

    print("debug: executing ragas evaluate\n")

    results = evaluate(
        dataset=dataset,
        metrics=metrics,
    )

    res_df = results.to_pandas()

    print("debug: result columns: \n\n", res_df.columns.tolist())

    # log per-query metrics
    for i, row in res_df.iterrows():
        logger.info(f"\nticket desc: {dataset[i]['question']}")
        logger.info(f"predicted: {dataset[i]['answer']}")
        logger.info(f"expected: {dataset[i]['reference'][0]}")
        logger.info(f"em: {row['exact_match']:.3f}")
        logger.info(f"rouge_l_fmeasure: {row['rouge_score(mode=fmeasure)']:.3f}")
        logger.info(f"bleu: {row['bleu_score']:.3f}")

    print("debug: evaluation results processed\n")

    return {
        "em": float(np.mean(results["exact_match"])),
        "rouge_l": float(np.mean(results["rouge_score(mode=fmeasure)"])),
        "bleu": float(np.mean(results["bleu_score"])),
        "per_query": [
            {
                "question": dataset[i]["question"],
                "predicted": dataset[i]["answer"],
                "expected": dataset[i]["reference"][0],
                "exact_match": row["exact_match"],
                "rouge_l_fmeasure": row["rouge_score(mode=fmeasure)"],
                "bleu": row["bleu_score"],
            }
            for i, row in res_df.iterrows()
        ],
    }