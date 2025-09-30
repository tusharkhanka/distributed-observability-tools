#!/bin/bash

# Quick Load Generator - Simple script to generate traces with correlation IDs

# Generate 10 user creation requests with correlation IDs
echo "🚀 Generating 10 user traces with correlation IDs..."

for i in {1..10}; do
    correlation_id="quick-load-$(date +%s)-$i"
    name="LoadTest$i"
    email="loadtest$i@example.com"
    
    echo "Creating user $i with correlation ID: $correlation_id"
    
    curl -X POST http://localhost:9001/api/v1/users \
        -H "Content-Type: application/json" \
        -H "x-correlation-id: $correlation_id" \
        -d "{\"name\": \"$name\", \"email\": \"$email\"}" \
        -s | jq '.'
    
    echo "---"
    sleep 1
done

echo "✅ Done! Check SigNoz UI for traces with correlation IDs starting with 'quick-load-'"
