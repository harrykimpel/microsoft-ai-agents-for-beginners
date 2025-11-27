#!/bin/bash

export OTEL_TRACES_EXPORTER=otlp
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
# US region
export OTEL_EXPORTER_OTLP_ENDPOINT='https://otlp.nr-data.net'
# EU region
#export OTEL_EXPORTER_OTLP_ENDPOINT='https://otlp.eu01.nr-data.net'
export OTEL_EXPORTER_OTLP_HEADERS="api-key=$NEW_RELIC_LICENSE_KEY_AI"
export OTEL_SERVICE_NAME="agent-travel-planner"

export OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true
export OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_METADATA=true
export OTEL_INSTRUMENTATION_GENAI_CAPTURE_TOOL_OUTPUT=true
export OTEL_INSTRUMENTATION_GENAI_CAPTURE_TOOL_INPUT=true

export OTLP_ENDPOINT='https://otlp.nr-data.net'
export OTLP_HEADERS="api-key=$NEW_RELIC_LICENSE_KEY_AI"

./01-dotnet-agent-framework.cs