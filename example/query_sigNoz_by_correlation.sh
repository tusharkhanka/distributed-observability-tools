#!/bin/bash
# SigNoz API Query Script - Searches traces by correlation_id

CORRELATION_ID="$1"

if [ -z "$CORRELATION_ID" ]; then
    echo "Usage: $0 <correlation_id>"
    echo "Example: $0 quick-load-1234567890-1"
    exit 1
fi

# Calculate timestamps (milliseconds)
START_TIME=$(( ($(date +%s) - 3600) * 1000 ))  # 1 hour ago
END_TIME=$(( ($(date +%s) + 60) * 1000 ))     # 1 minute from now

echo "🔍 Querying SigNoz for correlation_id: $CORRELATION_ID"
echo "🕒 Time range: $START_TIME to $END_TIME (milliseconds since epoch)"

curl -X POST http://localhost:8080/api/v4/query_range \
  -H "Content-Type: application/json" \
  -H "SIGNOZ-API-KEY: DZ0LDlU4WWnuCvcTOblMbpFI6KhbLucauRT/oYFDkTI=" \
  -d "{
    \"start\": $START_TIME,
    \"end\": $END_TIME,
    \"step\": 60,
    \"compositeQuery\": {
      \"queryType\": \"builder\",
      \"builderQueries\": {
        \"A\": {
          \"queryName\": \"A\",
          \"expression\": \"A\",
          \"dataSource\": \"traces\",
          \"aggregateOperator\": \"noop\",
          \"filters\": {
            \"items\": [{
              \"key\": {\"key\": \"correlation_id\", \"type\": \"tag\", \"isColumn\": true},
              \"op\": \"=\",
              \"value\": \"$CORRELATION_ID\"
            }]
          },
          \"selectColumns\": [
            {\"key\": \"serviceName\", \"type\": \"tag\", \"isColumn\": true},
            {\"key\": \"name\", \"type\": \"tag\", \"isColumn\": true},
            {\"key\": \"correlation_id\", \"type\": \"tag\", \"isColumn\": true},
            {\"key\": \"trace_id\", \"type\": \"tag\", \"isColumn\": true},
            {\"key\": \"duration_nano\", \"type\": \"tag\", \"isColumn\": true},
            {\"key\": \"status_code\", \"type\": \"tag\", \"isColumn\": true}
          ],
          \"limit\": 20,
          \"orderBy\": [{\"columnName\": \"timestamp\", \"order\": \"desc\"}]
        }
      }
    },
    \"dataSource\": \"traces\"
  }" | jq '.'
