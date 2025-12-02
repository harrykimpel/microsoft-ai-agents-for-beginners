# 📦 Import Required Libraries
# Standard library imports for system operations and random number generation
import os
from random import randint, uniform
import asyncio
import time
import uuid
import logging
import requests
import json
import uuid

# Third-party library for loading environment variables from .env file
from dotenv import load_dotenv

# 🤖 Import Microsoft Agent Framework Components
# ChatAgent: The main agent class for conversational AI
# OpenAIChatClient: Client for connecting to OpenAI-compatible APIs (including GitHub Models)
from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
from agent_framework.observability import setup_observability, get_tracer, get_meter

from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv._incubating.attributes.service_attributes import SERVICE_NAME
from opentelemetry.trace.span import format_trace_id

resource = Resource.create({SERVICE_NAME: os.environ.get("OTEL_SERVICE_NAME")})

# if not logging.getLogger().handlers:
#     logging.basicConfig(
#         level=os.getenv("LOG_LEVEL", "INFO"),
#         format="%(asctime)s | %(levelname)s | tools | %(message)s",
#     )
# logger = logging.getLogger("travel_agent")
# logger.debug("Logger initialized")
logger = logging.getLogger()
def setup_logging():
    # Create and set a global logger provider for the application.
    logger_provider = LoggerProvider(resource=resource)
    # Log processors are initialized with an exporter which is responsible
    #logger_provider.add_log_record_processor(BatchLogRecordProcessor(ConsoleLogExporter()))
    # Sets the global default logger provider
    set_logger_provider(logger_provider)
    # Create a logging handler to write logging records, in OTLP format, to the exporter.
    handler = LoggingHandler()
    # Attach the handler to the root logger. `getLogger()` with no arguments returns the root logger.
    # Events from all child loggers will be processed by this handler.
    #logger = logging.getLogger()
    logger.addHandler(handler)
    # Set the logging level to NOTSET to allow all records to be processed by the handler.
    logger.setLevel(logging.INFO)

# # Enable Agent Framework telemetry with console output (default behavior)
setup_observability(enable_sensitive_data=True, exporters=["otlp"])
setup_logging()
tracer = get_tracer()
meter = get_meter()

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

    with tracer.start_as_current_span("get_destination_from_list") as current_span:
        # Return a random destination from the list
        destination = destinations[randint(0, len(destinations) - 1)]
        logger.info("[get_destination_from_list] selected", extra={"destination": destination})
        current_span.set_attribute("destination", destination)
        pass
    
    return destination

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

    request_id = str(uuid.uuid4())
    t0 = time.time()
    logger.info("[get_weather] start", extra={"request_id": request_id, "city": location})
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        logger.error("[get_weather] missing API key", extra={"request_id": request_id})
        raise ValueError("Weather service not configured. OPENWEATHER_API_KEY environment variable is required.")
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        weather = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        result = f"Weather in {location}: {weather}, Temperature: {temp}°C (feels like {feels_like}°C), Humidity: {humidity}%"
        elapsed_ms = int((time.time() - t0) * 1000)
        logger.info(
            "[get_weather] complete",
            extra={"request_id": request_id, "city": location, "weather": weather, "temp": temp, "elapsed_ms": elapsed_ms},
        )
        return result
    except requests.exceptions.RequestException as e:
        logger.error("[get_weather] request_error", extra={"request_id": request_id, "city": location, "error": str(e)})
        return f"Error fetching weather data for {location}. Please check the city name."
    except KeyError as e:
        logger.error("[get_weather] parse_error", extra={"request_id": request_id, "city": location, "error": str(e)})
        return f"Error parsing weather data for {location}."
    #return f"The weather in {location} is cloudy with a high of 15°C."


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
model_id=os.environ.get("GITHUB_MODEL_ID")
openai_chat_client = OpenAIChatClient(
    base_url=os.environ.get("GITHUB_ENDPOINT"),
    api_key=os.environ.get("GITHUB_TOKEN"), 
    model_id=model_id
)
# openai_chat_client = OpenAIChatClient(
#     #base_url=os.environ.get("GITHUB_ENDPOINT"),
#     api_key=os.environ.get("OPENAI_API_KEY"), 
#     model_id=model_id
# )

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

entityGuid=os.environ.get("NEW_RELIC_ENTITY_GUID")

# 🚀 Run the Agent
# Send a message to the agent and get a response
# The agent will use its tools (get_random_destination) if needed
async def main():
    with tracer.start_as_current_span("main") as current_span:
        logger.info("[main] starting agent interaction")
        current_span.set_attribute("model_id", model_id)

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

        span_id = format(current_span.get_span_context().span_id, "016x")
        trace_id = format_trace_id(current_span.get_span_context().trace_id)

        input_tokens = response.usage_details.input_token_count
        output_tokens = response.usage_details.output_token_count

        logger.info("[agent_response]", extra={
            "newrelic.event.type": "LlmChatCompletionMessage", 
            #"appId": 1234567890,
            "appName": "agent-travel-planner",
            "entityGuid": entityGuid,
            "id": str(uuid.uuid4()), 
            "request_id": str(uuid.uuid4()),
            "span_id": span_id,
            "trace_id": trace_id,
            "response.model": model_id,
            "vendor": "openai",
            "ingest_source": "Python",
            "content": userPrompt,
            "role": "user",
            "sequence": 0,
            "is_response": False,
            "completion_id": str(uuid.uuid4()),
            "tags.aiEnabledApp": True,
            "tags.account": "AI-Observability",
            "tags.accountId": 4541509,
            "tags.trustedAccountId": 3882521})
        
        logger.info("[agent_response]", extra={
            "newrelic.event.type": "LlmChatCompletionMessage", 
            #"appId": 1234567890,
            "appName": "agent-travel-planner",
            "entityGuid": entityGuid,
            "id": str(uuid.uuid4()), 
            "request_id": str(uuid.uuid4()),
            "span_id": span_id,
            "trace_id": trace_id,
            "response.model": model_id,
            "vendor": "openai",
            "ingest_source": "Python",
            "content": text_content,
            "role": "assistant",
            "sequence": 1,
            "is_response": True,
            "completion_id": str(uuid.uuid4()),
            "tags.aiEnabledApp": True,
            "tags.account": "AI-Observability",
            "tags.accountId": 4541509,
            "tags.trustedAccountId": 3882521})
        
        logger.info("[agent_response]", extra={
            "newrelic.event.type": "LlmChatCompletionSummary", 
            #"appId": 1234567890,
            "appName": "agent-travel-planner",
            "entityGuid": entityGuid,
            "id": str(uuid.uuid4()), 
            "request_id": str(uuid.uuid4()),
            "span_id": span_id,
            "trace_id": trace_id,
            "request.model": model_id,
            "response.model": model_id,
            "token_count": input_tokens+output_tokens,
            "request.max_tokens": 0,
            "response.number_of_messages": 2,
            "response.choices.finish_reason": "FINISH",
            "vendor": "openai",
            "ingest_source": "Python",
            "tags.aiEnabledApp": True,
            "tags.account": "AI-Observability",
            "tags.accountId": 4541509,
            "tags.trustedAccountId": 3882521})
    
        pass


if __name__ == "__main__":
    asyncio.run(main())