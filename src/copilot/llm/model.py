# handles communication with ollama

import subprocess
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

class OllamaLLM:
    def __init__(self, model_name: str = "llama3.1"):
        self.model_name = model_name
        logger.info(f"ollama model initialized: {model_name}\n")

    def generate(self, prompt: str) -> str:
        try:
            logger.info("sending prompt to ollama\n")

            result = subprocess.run(
                ["ollama", "run", self.model_name],
                input=prompt,
                text=True,
                capture_output=True
            )

            if result.returncode != 0:
                raise RuntimeError(result.stderr)

            logger.info("response received from ollama\n")
            return result.stdout.strip()

        except Exception:
            logger.error("ollama generation failed\n", exc_info=True)
            raise