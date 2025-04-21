import asyncio
import os
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

OLLAMA_API_ENDPOINT = os.environ.get(
    "OLLAMA_OPENAI_ENDPOINT", "http://localhost:11434/v1"
)
MODEL_NAME = os.environ.get(
    "OLLAMA_MODEL", "qwen2.5-coder"
)  # Ensure this model is pulled in Ollama

ollama_provider = OpenAIProvider(base_url=OLLAMA_API_ENDPOINT, api_key="ollama")
ollama_model_config = OpenAIModel(model_name=MODEL_NAME, provider=ollama_provider)

scenario = {
    "name": "Should know about capital cities",
    "given": "What is the capital of France?",
    "then": "Paris",
}


async def get_llm_response(prompt: str) -> str:
    """Sends a prompt to the configured LLM and returns the text response."""
    agent = Agent(model=ollama_model_config)
    try:
        print(f"--- Sending prompt to {MODEL_NAME}: '{prompt}' ---")
        agent_run = await agent.run(prompt)
        result_output = agent_run.output

        print(f"--- Received response: '{result_output}' ---")
        return result_output
    except Exception as e:
        print(f"--- Error interacting with LLM: {e} ---")
        return f"Error: {e}"


def check_response(response: str, then: str) -> bool:
    """Checks if the response contains the expected substring (case-insensitive)."""
    return then.lower() in response.lower()


async def main():
    print("--- Starting Minimal BDD-Inspired Check ---")
    print(f"Using Model: {MODEL_NAME} via {OLLAMA_API_ENDPOINT}")
    print(f"Scenario: {scenario['name']}")

    llm_response = await get_llm_response(scenario["given"])

    is_pass = check_response(llm_response, scenario["then"])

    print("\n--- Test Result ---")
    print(f"Given: '{scenario['given']}'")
    print(f"Response: '{llm_response}'")
    print(f"Expectation: Response should contain '{scenario['then']}'")
    print(f"Result: {'PASS' if is_pass else 'FAIL'}")
    print("--- Check Complete ---")


if __name__ == "__main__":
    print(f"Using Ollama via OpenAI-compatible endpoint: {OLLAMA_API_ENDPOINT}")
    print(f"Ensure Ollama server is running and model ({MODEL_NAME}) is pulled.")
    asyncio.run(main())
