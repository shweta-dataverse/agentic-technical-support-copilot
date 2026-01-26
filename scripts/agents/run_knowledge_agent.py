# scripts/test_knowledge_agent.py

from copilot.agents.knowledge_agent import KnowledgeAgent
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

def main():
    logger.info("initializing knowledge agent\n")
    agent = KnowledgeAgent()

    query = "Issue description: Axis_1 (Linear Slider) faulted during positioning. MC_MoveAbsolute returns Error=TRUE and ErrorID=16#8001." \
    "Issue title: Motion Control: ErrorID 16#8001 Low SW Limit"
    logger.info(f"testing knowledge agent with query: {query}\n")

    answer = agent.retrieve(query)

    print("\nknowledge agent answer:\n")
    print(answer)
    print("\n")

if __name__ == "__main__":
    main()