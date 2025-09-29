#!/bin/bash

# Traffic generation script using curl commands
# This script generates distributed traces across all three microservices

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Service endpoints
USER_SERVICE="http://localhost:9001"
ORDER_SERVICE="http://localhost:9002"
INVENTORY_SERVICE="http://localhost:9003"

# Function to generate correlation ID
generate_correlation_id() {
    echo "$(uuidgen | tr '[:upper:]' '[:lower:]')"
}

# Function to generate request ID
generate_request_id() {
    echo "$(uuidgen | tr '[:upper:]' '[:lower:]')"
}

echo "🚀 Starting distributed trace generation..."
echo "=================================================="

# Check if services are healthy
echo -e "\n${BLUE}🔍 Checking service health...${NC}"
curl -s "$USER_SERVICE/health" | jq -r '.status' > /dev/null && echo "✅ User service is healthy"
curl -s "$ORDER_SERVICE/health" | jq -r '.status' > /dev/null && echo "✅ Order service is healthy"
curl -s "$INVENTORY_SERVICE/health" | jq -r '.status' > /dev/null && echo "✅ Inventory service is healthy"

# Array to store created user IDs
declare -a USER_IDS=()

echo -e "\n${BLUE}📝 Phase 1: Creating users...${NC}"

# Create users
for i in {1..3}; do
    CORRELATION_ID=$(generate_correlation_id)
    REQUEST_ID=$(generate_request_id)
    
    echo -e "${BLUE}🔵 Creating user $i (correlation_id: $CORRELATION_ID)${NC}"
    
    USER_DATA=$(cat <<EOF
{
    "name": "User $i",
    "email": "user$i@example.com"
}
EOF
)
    
    RESPONSE=$(curl -s -X POST "$USER_SERVICE/api/v1/users" \
        -H "Content-Type: application/json" \
        -H "x-correlation-id: $CORRELATION_ID" \
        -H "x-request-id: $REQUEST_ID" \
        -d "$USER_DATA")
    
    USER_ID=$(echo "$RESPONSE" | jq -r '.user_id')
    USER_IDS+=("$USER_ID")
    
    echo "✅ User created: $USER_ID"
    sleep 1
done

echo -e "\n${YELLOW}📦 Phase 2: Creating orders (distributed traces)...${NC}"

# Create orders that flow through all services
for USER_ID in "${USER_IDS[@]}"; do
    CORRELATION_ID=$(generate_correlation_id)
    REQUEST_ID=$(generate_request_id)
    
    echo -e "${YELLOW}🟡 Creating order for user $USER_ID (correlation_id: $CORRELATION_ID)${NC}"
    
    ORDER_DATA=$(cat <<EOF
{
    "user_id": "$USER_ID",
    "items": [
        {"product_id": "laptop-001", "quantity": 1},
        {"product_id": "mouse-002", "quantity": 2}
    ]
}
EOF
)
    
    RESPONSE=$(curl -s -X POST "$USER_SERVICE/api/v1/users/$USER_ID/orders" \
        -H "Content-Type: application/json" \
        -H "x-correlation-id: $CORRELATION_ID" \
        -H "x-request-id: $REQUEST_ID" \
        -d "$ORDER_DATA")
    
    ORDER_ID=$(echo "$RESPONSE" | jq -r '.order_id')
    echo "✅ Order created: $ORDER_ID"
    sleep 2
done

echo -e "\n${GREEN}🔍 Phase 3: Querying user orders (read traces)...${NC}"

# Query user orders
for USER_ID in "${USER_IDS[@]}"; do
    CORRELATION_ID=$(generate_correlation_id)
    REQUEST_ID=$(generate_request_id)
    
    echo -e "${GREEN}🟢 Getting orders for user $USER_ID (correlation_id: $CORRELATION_ID)${NC}"
    
    RESPONSE=$(curl -s -X GET "$USER_SERVICE/api/v1/users/$USER_ID/orders" \
        -H "x-correlation-id: $CORRELATION_ID" \
        -H "x-request-id: $REQUEST_ID")
    
    ORDER_COUNT=$(echo "$RESPONSE" | jq -r '.orders | length')
    echo "✅ Retrieved $ORDER_COUNT orders for user $USER_ID"
    sleep 1
done

echo -e "\n${PURPLE}📋 Phase 4: Direct inventory checks...${NC}"

# Direct inventory service calls
PRODUCTS=("laptop-001" "mouse-002" "keyboard-003" "monitor-004")

for PRODUCT in "${PRODUCTS[@]}"; do
    CORRELATION_ID=$(generate_correlation_id)
    REQUEST_ID=$(generate_request_id)
    
    echo -e "${PURPLE}🟣 Checking inventory for $PRODUCT (correlation_id: $CORRELATION_ID)${NC}"
    
    RESPONSE=$(curl -s -X GET "$INVENTORY_SERVICE/api/v1/inventory/$PRODUCT" \
        -H "x-correlation-id: $CORRELATION_ID" \
        -H "x-request-id: $REQUEST_ID")
    
    QUANTITY=$(echo "$RESPONSE" | jq -r '.available_quantity')
    echo "✅ Product $PRODUCT has $QUANTITY units available"
    sleep 1
done

echo -e "\n${PURPLE}📦 Getting all inventory...${NC}"
CORRELATION_ID=$(generate_correlation_id)
REQUEST_ID=$(generate_request_id)

RESPONSE=$(curl -s -X GET "$INVENTORY_SERVICE/api/v1/inventory" \
    -H "x-correlation-id: $CORRELATION_ID" \
    -H "x-request-id: $REQUEST_ID")

ITEM_COUNT=$(echo "$RESPONSE" | jq -r '.inventory | length')
echo "✅ Retrieved $ITEM_COUNT inventory items"

echo -e "\n=================================================="
echo -e "${GREEN}✅ Distributed trace generation completed!${NC}"
echo ""
echo "📊 Summary:"
echo "   - Users created: ${#USER_IDS[@]}"
echo "   - Orders created: ${#USER_IDS[@]}"
echo "   - Inventory checks: ${#PRODUCTS[@]}"
echo ""
echo "🔍 Check SigNoz at http://localhost:8080 for distributed traces!"
echo "   - Look for traces with the correlation IDs printed above"
echo "   - Traces should show spans across user-service → order-service → inventory-service"
echo ""
echo "🌐 Service endpoints:"
echo "   - User Service: $USER_SERVICE"
echo "   - Order Service: $ORDER_SERVICE" 
echo "   - Inventory Service: $INVENTORY_SERVICE"
echo "   - SigNoz UI: http://localhost:8080"
