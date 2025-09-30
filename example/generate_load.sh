#!/bin/bash

# Load Testing Script for Distributed Observability Tools
# This script generates HTTP requests with correlation IDs to create traces in SigNoz

set -e

# Configuration
USER_SERVICE_URL="http://localhost:9001"
ORDER_SERVICE_URL="http://localhost:9002"
INVENTORY_SERVICE_URL="http://localhost:9003"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to generate random correlation ID
generate_correlation_id() {
    echo "load-test-$(date +%s)-$(shuf -i 1000-9999 -n 1)"
}

# Function to generate random user data
generate_user_data() {
    local names=("Alice" "Bob" "Charlie" "Diana" "Eve" "Frank" "Grace" "Henry" "Ivy" "Jack")
    local domains=("example.com" "test.com" "demo.org" "sample.net")
    
    local name=${names[$RANDOM % ${#names[@]}]}
    local domain=${domains[$RANDOM % ${#domains[@]}]}
    local timestamp=$(date +%s)
    
    echo "{\"name\": \"$name Load Test\", \"email\": \"${name,,}.${timestamp}@${domain}\"}"
}

# Function to generate random order data
generate_order_data() {
    local user_id=$1
    local products=("laptop" "mouse" "keyboard" "monitor" "headphones")
    local product=${products[$RANDOM % ${#products[@]}]}
    local quantity=$((RANDOM % 3 + 1))
    
    echo "{\"user_id\": $user_id, \"product_name\": \"$product\", \"quantity\": $quantity}"
}

# Function to make HTTP request with correlation ID
make_request() {
    local method=$1
    local url=$2
    local correlation_id=$3
    local data=$4
    local description=$5
    
    echo -e "${BLUE}[$(date '+%H:%M:%S')] $description${NC}"
    echo -e "${YELLOW}Correlation ID: $correlation_id${NC}"
    
    if [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
            -H "Content-Type: application/json" \
            -H "x-correlation-id: $correlation_id" \
            -d "$data")
    else
        response=$(curl -s -w "\n%{http_code}" -X GET "$url" \
            -H "x-correlation-id: $correlation_id")
    fi
    
    # Extract response body and status code
    response_body=$(echo "$response" | head -n -1)
    status_code=$(echo "$response" | tail -n 1)
    
    if [ "$status_code" -ge 200 ] && [ "$status_code" -lt 300 ]; then
        echo -e "${GREEN}✅ Success ($status_code): $response_body${NC}"
        echo "$response_body"
    else
        echo -e "${RED}❌ Error ($status_code): $response_body${NC}"
        echo ""
    fi
    
    echo "---"
}

# Function to create a complete distributed trace
create_distributed_trace() {
    local base_correlation_id=$(generate_correlation_id)
    
    echo -e "${BLUE}🚀 Creating distributed trace with base correlation ID: $base_correlation_id${NC}"
    echo
    
    # Step 1: Create a user
    local user_data=$(generate_user_data)
    local user_response=$(make_request "POST" "$USER_SERVICE_URL/api/v1/users" "${base_correlation_id}-user" "$user_data" "Creating user")
    
    # Extract user ID from response
    local user_id=$(echo "$user_response" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    
    if [ -n "$user_id" ]; then
        echo -e "${GREEN}Created user with ID: $user_id${NC}"
        
        # Step 2: Create an order for the user
        local order_data=$(generate_order_data "$user_id")
        make_request "POST" "$ORDER_SERVICE_URL/api/v1/orders" "${base_correlation_id}-order" "$order_data" "Creating order for user $user_id"
        
        # Step 3: Check inventory
        make_request "GET" "$INVENTORY_SERVICE_URL/api/v1/inventory" "${base_correlation_id}-inventory" "" "Checking inventory"
        
        # Step 4: Get user details
        make_request "GET" "$USER_SERVICE_URL/api/v1/users/$user_id" "${base_correlation_id}-get-user" "" "Getting user $user_id details"
    else
        echo -e "${RED}Failed to extract user ID, skipping order creation${NC}"
    fi
    
    echo
}

# Function to create simple user traces
create_user_traces() {
    local count=$1
    echo -e "${BLUE}🔄 Creating $count user traces...${NC}"
    echo
    
    for i in $(seq 1 $count); do
        local correlation_id=$(generate_correlation_id)
        local user_data=$(generate_user_data)
        make_request "POST" "$USER_SERVICE_URL/api/v1/users" "$correlation_id" "$user_data" "Creating user $i/$count"
        sleep 0.5
    done
}

# Function to create health check traces
create_health_traces() {
    local correlation_id=$(generate_correlation_id)
    echo -e "${BLUE}🏥 Creating health check traces...${NC}"
    echo
    
    make_request "GET" "$USER_SERVICE_URL/health" "${correlation_id}-user-health" "" "User service health check"
    make_request "GET" "$ORDER_SERVICE_URL/health" "${correlation_id}-order-health" "" "Order service health check"
    make_request "GET" "$INVENTORY_SERVICE_URL/health" "${correlation_id}-inventory-health" "" "Inventory service health check"
}

# Function to run continuous load
run_continuous_load() {
    local duration=$1
    local interval=${2:-2}
    
    echo -e "${BLUE}🔄 Running continuous load for $duration seconds (interval: ${interval}s)...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo
    
    local end_time=$(($(date +%s) + duration))
    local counter=1
    
    while [ $(date +%s) -lt $end_time ]; do
        echo -e "${BLUE}--- Load iteration $counter ---${NC}"
        
        # Mix of different request types
        case $((counter % 4)) in
            0)
                create_distributed_trace
                ;;
            1)
                create_user_traces 2
                ;;
            2)
                create_health_traces
                ;;
            3)
                # Random inventory check
                local correlation_id=$(generate_correlation_id)
                make_request "GET" "$INVENTORY_SERVICE_URL/api/v1/inventory" "$correlation_id" "" "Random inventory check"
                ;;
        esac
        
        counter=$((counter + 1))
        sleep $interval
    done
    
    echo -e "${GREEN}✅ Continuous load completed${NC}"
}

# Main script
main() {
    echo -e "${GREEN}🚀 Distributed Observability Load Testing Script${NC}"
    echo -e "${YELLOW}This script will generate HTTP requests with correlation IDs to create traces in SigNoz${NC}"
    echo
    
    # Check if services are running
    echo -e "${BLUE}🔍 Checking service availability...${NC}"
    
    for service in "$USER_SERVICE_URL/health" "$ORDER_SERVICE_URL/health" "$INVENTORY_SERVICE_URL/health"; do
        if curl -s "$service" > /dev/null; then
            echo -e "${GREEN}✅ $service is available${NC}"
        else
            echo -e "${RED}❌ $service is not available${NC}"
            echo -e "${YELLOW}Please make sure all services are running with: docker compose up -d${NC}"
            exit 1
        fi
    done
    echo
    
    # Show menu
    echo -e "${BLUE}Choose an option:${NC}"
    echo "1. Create 1 distributed trace (user → order → inventory)"
    echo "2. Create 5 user traces"
    echo "3. Create health check traces"
    echo "4. Run continuous load (30 seconds)"
    echo "5. Run continuous load (60 seconds)"
    echo "6. Run continuous load (custom duration)"
    echo "7. Create mixed load (recommended for demo)"
    echo
    
    read -p "Enter your choice (1-7): " choice
    
    case $choice in
        1)
            create_distributed_trace
            ;;
        2)
            create_user_traces 5
            ;;
        3)
            create_health_traces
            ;;
        4)
            run_continuous_load 30
            ;;
        5)
            run_continuous_load 60
            ;;
        6)
            read -p "Enter duration in seconds: " duration
            read -p "Enter interval between requests (default 2s): " interval
            interval=${interval:-2}
            run_continuous_load $duration $interval
            ;;
        7)
            echo -e "${BLUE}🎯 Creating mixed load for demo...${NC}"
            echo
            create_distributed_trace
            sleep 2
            create_user_traces 3
            sleep 2
            create_health_traces
            sleep 2
            create_distributed_trace
            echo -e "${GREEN}✅ Mixed load completed${NC}"
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
    
    echo
    echo -e "${GREEN}🎉 Load generation completed!${NC}"
    echo -e "${YELLOW}Check SigNoz UI at http://localhost:8080 to see the traces${NC}"
    echo -e "${YELLOW}Search for correlation IDs starting with 'load-test-' to find your traces${NC}"
}

# Run the script
main "$@"
