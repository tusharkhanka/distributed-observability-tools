#!/bin/bash

# Load Generation Script for Published Package Testing
# Generates requests with correlation IDs to test published package functionality

# Generate 5 test requests with correlation IDs
echo "🚀 Generating 5 test requests with correlation IDs..."
echo "📊 Testing published distributed-observability-tools package"
echo ""

for i in {1..5}; do
    timestamp=$(date +%s)
    correlation_id="pkg-test-${timestamp}-$i"
    name="TestUser$i"
    email="testuser$i@example.com"

    echo "📤 Request $i: Creating user '$name' with correlation ID '$correlation_id'"

    # Send POST request to create user with correlation ID header
    response=$(curl -s -X POST http://localhost:9001/api/v1/users \
        -H "Content-Type: application/json" \
        -H "x-correlation-id: $correlation_id" \
        -d "{\"name\": \"$name\", \"email\": \"$email\"}")

    # Check if request was successful
    if echo "$response" | jq -e '.id' >/dev/null 2>&1; then
        user_id=$(echo "$response" | jq -r '.id')
        echo "✅ Success: Created user ID $user_id"
    else
        echo "❌ Request failed - check logs"
    fi

    echo "---"

    # Brief pause between requests
    sleep 1
done

echo ""
echo "✨ Load generation complete!"
echo "🔍 Check service logs to verify:"
echo "   - Correlation IDs are detected and set as span attributes"
echo "   - Traces are exported successfully"
echo "   - Published package is working correctly"
