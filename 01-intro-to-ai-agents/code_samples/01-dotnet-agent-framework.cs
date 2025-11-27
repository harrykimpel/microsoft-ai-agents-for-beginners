#!/usr/bin/dotnet run

#:package Microsoft.Extensions.AI@10.*
#:package Microsoft.Agents.AI.OpenAI@1.*-*
#:package OpenTelemetry@1.14.*
#:package OpenTelemetry.Exporter.OpenTelemetryProtocol@1.14.*

using System.ClientModel;
using System.ComponentModel;
using System.Diagnostics;

using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;

using OpenAI;

using OpenTelemetry;
using OpenTelemetry.Trace;
using OpenTelemetry.Logs;
using OpenTelemetry.Resources;

const string ActivitySourceName = "agent-travel-planner";
const string ActivitySourceVersion = "1.0.0";

var otlpEndpoint = Environment.GetEnvironmentVariable("OTEL_EXPORTER_OTLP_ENDPOINT") ?? "https://otlp.nr-data.net";
var otlpHeaders = Environment.GetEnvironmentVariable("OTEL_EXPORTER_OTLP_HEADERS") ?? throw new InvalidOperationException("OTEL_EXPORTER_OTLP_HEADERS is not set.");

// Create a TracerProvider that exports to the console
using var tracerProvider = Sdk.CreateTracerProviderBuilder()
    .AddSource(ActivitySourceName)
    .ConfigureResource(resource =>
        resource.AddService(
          serviceName: ActivitySourceName,
          serviceVersion: ActivitySourceVersion))
    .AddOtlpExporter( options =>
    {
        options.Endpoint = new Uri(otlpEndpoint);
        options.Headers = otlpHeaders;
    })
    .Build();

// Create a logger factory with OpenTelemetry
using var loggerFactory = LoggerFactory.Create(builder =>
{
    builder.AddOpenTelemetry(options =>
    {
        options.AddOtlpExporter( options =>
        {
            options.Endpoint = new Uri(otlpEndpoint);
            options.Headers = otlpHeaders;
        });
    });
});

// Get a logger instance
var logger = loggerFactory.CreateLogger<Program>();

//ActivitySource activitySource = new ActivitySource(ActivitySourceName, ActivitySourceVersion);

// Extract configuration from environment variables
// Retrieve the GitHub Models API endpoint, defaults to https://models.github.ai/inference if not specified
// Retrieve the model ID, defaults to openai/gpt-5-mini if not specified
// Retrieve the GitHub token for authentication, throws exception if not specified
var github_endpoint = Environment.GetEnvironmentVariable("GH_ENDPOINT") ?? "https://models.github.ai/inference";
var github_model_id = Environment.GetEnvironmentVariable("GH_MODEL_ID") ?? "gpt-4.1-mini";
var github_token = Environment.GetEnvironmentVariable("GITHUB_TOKEN") ?? throw new InvalidOperationException("GITHUB_TOKEN is not set.");

var tracer = tracerProvider.GetTracer(ActivitySourceName, ActivitySourceVersion);
using var span = tracer.StartActiveSpan("hello-span");
//using (var mainActivity =  activitySource.StartActivity("agent-activity-travel-planner"))
{
    // Tool Function: Random Destination Generator
    // This static method will be available to the agent as a callable tool
    // The [Description] attribute helps the AI understand when to use this function
    // This demonstrates how to create custom tools for AI agents
    [Description("Provides a random vacation destination.")]
    static string GetRandomDestination()
    {
        // List of popular vacation destinations around the world
        // The agent will randomly select from these options
        var destinations = new List<string>
        {
            "Garmisch-Partenkirchen, Germany",
            "Munich, Germany",
            "Paris, France",
            "Tokyo, Japan",
            "New York City, USA",
            "Sydney, Australia",
            "Rome, Italy",
            "Barcelona, Spain",
            "Cape Town, South Africa",
            "Rio de Janeiro, Brazil",
            "Bangkok, Thailand",
            "Vancouver, Canada"
        };

        // Generate random index and return selected destination
        // Uses System.Random for simple random selection
        var random = new Random();
        int index = random.Next(destinations.Count);
        return destinations[index];
    }

    [Description("Get the weather for a given location.")]
    static string GetWeather([Description("The location to get the weather for.")] string location)
        => $"The weather in {location} is cloudy with a high of 15°C.";

    [Description("The current date and time.")]
    static string GetDateTime()
        => DateTime.Now.ToString();

    // Configure OpenAI Client Options
    // Create configuration options to point to GitHub Models endpoint
    // This redirects OpenAI client calls to GitHub's model inference service
    var openAIOptions = new OpenAIClientOptions()
    {
        Endpoint = new Uri(github_endpoint)
    };

    // Initialize OpenAI Client with GitHub Models Configuration
    // Create OpenAI client using GitHub token for authentication
    // Configure it to use GitHub Models endpoint instead of OpenAI directly
    var openAIClient = new OpenAIClient(new ApiKeyCredential(github_token), openAIOptions);

    // Create AI Agent with Travel Planning Capabilities
    // Initialize complete agent pipeline: OpenAI client → Chat client → AI agent
    // Configure agent with name, instructions, and available tools
    // The agent can now plan trips using the GetRandomDestination function
    AIAgent agent = openAIClient
        .GetChatClient(github_model_id)
        .CreateAIAgent(
            instructions: "You are a helpful AI Agent that can help plan vacations for customers at random destinations",
            tools: [
                AIFunctionFactory.Create(GetRandomDestination, name: nameof(GetRandomDestination)),
                AIFunctionFactory.Create(GetWeather, name: nameof(GetWeather)),
                AIFunctionFactory.Create(GetDateTime, name: nameof(GetDateTime))
            ]
        )
        .AsBuilder()
        .UseOpenTelemetry(sourceName: ActivitySourceName)
        .Build();

    // Execute Agent: Plan a Day Trip
    // Run the agent with streaming enabled for real-time response display
    // Shows the agent's thinking and response as it generates the content
    // Provides better user experience with immediate feedback
    string userPrompt = "Plan me a day trip with activities and calculate the current weather at the destination. Mention the current date and time of the plan.";
    await foreach (var update in agent.RunStreamingAsync(userPrompt))
    {
        await Task.Delay(10);
        Console.Write(update);
        //logger.LogInformation("Agent Update: "+ update);
    }
} // End of Activity Scope

var activity = Activity.Current;
var logRecord = "{ \"Message\": \"Agent run completed.\", \"newrelic.eventType\": \"LLMxxxEvent\" }";
logger.LogInformation(logRecord);
logger.LogInformation("Activity TraceId: " + activity?.TraceId);
if (activity != null)
{
    var inputTokens = activity?.GetTagItem("gen_ai.usage.input_tokens");
    var finish_reasons = activity?.GetTagItem("gen_ai.usage.finish_reasons");
    var attributes = new Dictionary<string, object>
            {
                { "id", 1 },
                { "request_id", 1 },
                { "span_id", activity.SpanId.ToString() },
                { "trace_id", activity.TraceId.ToString() },
                { "operation.name", activity.DisplayName },
                { "operation.type", "LLM" },
                { "request.type", "chat.completion" },
                { "response.type", "chat.completion" },
                { "request.vendor", "GitHubModels" },
                { "response.vendor", "GitHubModels" },
                { "request.model", github_model_id },
                { "response.model", github_model_id },
                { "token_count", inputTokens},
                { "request.max_tokens", inputTokens},
                { "response.number_of_messages", 2 },
                { "response.choices.finish_reason", finish_reasons },
                { "vendor", "GitHubModels" },
                { "ingest_source", "DotNet" },
                { "tags.aiEnabledApp", true },
                // { "duration", (float)segment.DurationOrZero.TotalMilliseconds },
                //{ "llm.<user_defined_metadata>", "Pulled from Transaction metadata in RecordLlmEvent" },
                //{ "response.headers.<vendor_specific_headers>", "See LLM headers below" },
            };
}

tracerProvider.ForceFlush();
tracerProvider.Dispose();
loggerFactory.Dispose();

// wait for 5 minutes before exiting
//await Task.Delay(TimeSpan.FromMinutes(5));