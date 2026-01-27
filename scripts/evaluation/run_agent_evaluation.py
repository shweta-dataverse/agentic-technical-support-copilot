# copilot/evaluation/run_agent_evaluation.py

import pandas as pd
import mlflow
from copilot.evaluation.agent_generation_metrics import evaluate_generation
from copilot.utils.logger import get_logger
from pathlib import Path
import json

logger = get_logger(__name__)

EVAL_CSV_PATH = Path("data/evaluation/ticket_evaluation_data.csv")

def run_agent_evaluation():
    """
    run evaluation of agent-generated responses using ragas metrics
    logs results and metrics to mlflow
    """

    logger.info("\nstarting agent evaluation workflow...\n")

    df = pd.read_csv(EVAL_CSV_PATH)

    # prepare per-query list for ragas
    queries = [
        {
            "question": row["description"],
            "expected_answer": row["actual_resolution"],
            "predicted_answer": row["predicted_resolution"]
        }
        for _, row in df.iterrows()
    ]

    # log parameters
    mlflow.set_experiment("agent_generation_evaluation")
    with mlflow.start_run(run_name="run_generation_eval"):

        mlflow.log_param("num_tickets_evaluated", len(df))
        logger.info(f"\nevaluating {len(df)} tickets...\n")

        # compute generation metrics via ragas
        results = evaluate_generation(
            queries=queries,
            pred_key="predicted_answer",
            gold_key="expected_answer"
        )

        # log aggregate metrics
        mlflow.log_metrics({
            "avg_exact_match": results["em"],
            "avg_rouge_l": results["rouge_l"],
            "avg_bleu": results["bleu"],
        })

        # save per-query metrics as artifact
        per_query_path = "data/evaluation/agent_eval_per_query.json"
        Path(per_query_path).parent.mkdir(parents=True, exist_ok=True)

        with open(per_query_path, "w") as f:
            json.dump(results["per_query"], f, indent=2)

        mlflow.log_artifact(per_query_path, artifact_path="per_query_metrics")

        logger.info("\nevaluation metrics logged to mlflow\n")

    logger.info("\nagent evaluation run completed\n")


if __name__ == "__main__":
    run_agent_evaluation()