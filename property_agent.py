import asyncio
import logging
import os
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.mcp import MCPServerHTTP
from logging import  info


land_registry_mcp= MCPServerHTTP(url="http://localhost:8000/sse")

OLLAMA_API_ENDPOINT = os.environ.get(
    "OLLAMA_OPENAI_ENDPOINT", "http://localhost:11434/v1"
)
MODEL_NAME = os.environ.get(
    "OLLAMA_MODEL", "qwen2.5-coder"
)  # Ensure this model is pulled in Ollama

ollama_provider = OpenAIProvider(base_url=OLLAMA_API_ENDPOINT, api_key="ollama")
ollama_model_config = OpenAIModel(model_name=MODEL_NAME, provider=ollama_provider)
property_agent = Agent(model=ollama_model_config, mcp_servers=[land_registry_mcp])


scenario = {
    "name": "Returns average house price for UK locations given dates",
    "given": "What is the average house price for Bristol in January 2025?",
    "then": "£357,721",
}


def check_response(response: str, then: str) -> bool:
    """Checks if the response contains the expected substring (case-insensitive)."""
    return then.lower() in response.lower()


async def main():
    print("--- Starting Minimal BDD-Inspired Check ---")
    print(f"Using Model: {MODEL_NAME} via {OLLAMA_API_ENDPOINT}")
    print(f"Scenario: {scenario['name']}")
    async with property_agent.run_mcp_servers():
        llm_response = await property_agent.run(scenario["given"])
        print(llm_response.output)

        is_pass = check_response(llm_response.output, scenario["then"])

    print("\n--- Test Result ---")
    print(f"Given: '{scenario['given']}'")
    print(f"Response: '{llm_response}'")
    print(f"Expectation: Response should contain '{scenario['then']}'")
    print(f"Result: {'PASS' if is_pass else 'FAIL'}")
    print("--- Check Complete ---")


if __name__ == "__main__":
    asyncio.run(main())
