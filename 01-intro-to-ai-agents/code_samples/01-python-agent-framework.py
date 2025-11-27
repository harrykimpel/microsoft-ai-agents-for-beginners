# 📦 Import Required Libraries
# Standard library imports for system operations and random number generation
import os
from random import randint, uniform
import asyncio
import time

# Third-party library for loading environment variables from .env file
from dotenv import load_dotenv

# 🤖 Import Microsoft Agent Framework Components
# ChatAgent: The main agent class for conversational AI
# OpenAIChatClient: Client for connecting to OpenAI-compatible APIs (including GitHub Models)
from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
from agent_framework.observability import setup_observability

# Enable Agent Framework telemetry with console output (default behavior)
setup_observability(enable_sensitive_data=True, exporters=["otlp"])

# 🔧 Load Environment Variables
# This loads configuration from a .env file in the project root
# Required variables: GITHUB_ENDPOINT, GITHUB_TOKEN, GITHUB_MODEL_ID
load_dotenv()

# 🎲 Tool Function: Random Destination Generator
# This function will be available to the agent as a tool
# The agent can call this function to get random vacation destinations
def get_random_destination() -> str:
    """Get a random vacation destination.
    
    Returns:
        str: A randomly selected destination from our predefined list
    """
    # List of popular vacation destinations around the world
    destinations = [
        "Garmisch-Partenkirchen, Germany",
        "Munich, Germany",
        "Barcelona, Spain",
        "Paris, France", 
        "Berlin, Germany",
        "Tokyo, Japan",
        "Sydney, Australia",
        "New York, USA",
        "Cairo, Egypt",
        "Cape Town, South Africa",
        "Rio de Janeiro, Brazil",
        "Bali, Indonesia"
    ]

    # Simulate network latency with a small random sleep
    delay_seconds = uniform(0, 0.99)
    time.sleep(delay_seconds)

    # Return a random destination from the list
    return destinations[randint(0, len(destinations) - 1)]

# Tool Function: Get weather for a location
def get_weather(location: str) -> str:
    """Get the weather for a given location.

    Args:
        location: The location to get the weather for.
    Returns:
        A short weather description string.
    """

    # Simulate network latency with a small random float sleep
    delay_seconds = uniform(0.3, 3.7)
    time.sleep(delay_seconds)

    # fail every now and then to simulate real-world API unreliability
    if randint(1, 10) > 7:
        raise Exception("Weather service is currently unavailable. Please try again later.")

    return f"The weather in {location} is cloudy with a high of 15°C."


# Tool Function: Get current date and time
def get_datetime() -> str:
    """Return the current date and time as an ISO-like string."""
    from datetime import datetime

    # Simulate network latency with a small random float sleep
    delay_seconds = uniform(0.10, 5.0)
    time.sleep(delay_seconds)

    return datetime.now().isoformat(sep=' ', timespec='seconds')

# 🔗 Create OpenAI Chat Client for GitHub Models
# This client connects to GitHub Models API (OpenAI-compatible endpoint)
# Environment variables required:
# - GITHUB_ENDPOINT: API endpoint URL (usually https://models.inference.ai.azure.com)
# - GITHUB_TOKEN: Your GitHub personal access token
# - GITHUB_MODEL_ID: Model to use (e.g., gpt-4o-mini, gpt-4o)
openai_chat_client = OpenAIChatClient(
    base_url=os.environ.get("GITHUB_ENDPOINT"),
    api_key=os.environ.get("GITHUB_TOKEN"), 
    model_id=os.environ.get("GITHUB_MODEL_ID")
)

# 🤖 Create the Travel Planning Agent
# This creates a conversational AI agent with specific capabilities:
# - chat_client: The AI model client for generating responses
# - instructions: System prompt that defines the agent's personality and role
# - tools: List of functions the agent can call to perform actions
agent = ChatAgent(
    chat_client=openai_chat_client,
    instructions="You are a helpful AI Agent that can help plan vacations for customers at random destinations.",
    tools=[get_random_destination, get_weather, get_datetime]  # Tool functions available to the agent
)

# 🚀 Run the Agent
# Send a message to the agent and get a response
# The agent will use its tools (get_random_destination) if needed
async def main():
    userPrompt = "Plan me a day trip with activities and calculate the current weather at the destination. Mention the current date and time of the plan.";
    response = await agent.run(userPrompt)

    # 📖 Extract and Display the Travel Plan
    # Get the last message from the conversation (agent's response)s
    last_message = response.messages[-1]
    # Extract the text content from the message
    text_content = last_message.contents[0].text
    # Display the formatted travel plan
    print("🏖️ Travel plan:")
    print(text_content)

if __name__ == "__main__":
    asyncio.run(main())