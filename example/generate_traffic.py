#!/usr/bin/env python3
"""
Traffic generation script for distributed observability demo.

This script generates realistic API traffic across the microservices to create
distributed traces that demonstrate the observability tools package.

The script creates:
1. Users via user-service
2. Orders that flow through user-service → order-service → inventory-service
3. User order queries to generate read traces
4. Direct calls to individual services for comparison
"""

import requests
import json
import time
import random
import uuid
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Service endpoints
USER_SERVICE = "http://localhost:9001"
ORDER_SERVICE = "http://localhost:9002"
INVENTORY_SERVICE = "http://localhost:9003"

# Sample data for realistic traffic
SAMPLE_USERS = [
    {"name": "Alice Johnson", "email": "alice@example.com"},
    {"name": "Bob Smith", "email": "bob@example.com"},
    {"name": "Carol Davis", "email": "carol@example.com"},
    {"name": "David Wilson", "email": "david@example.com"},
    {"name": "Eve Brown", "email": "eve@example.com"},
]

SAMPLE_PRODUCTS = [
    {"product_id": "laptop-001", "quantity": 2},
    {"product_id": "mouse-002", "quantity": 1},
    {"product_id": "keyboard-003", "quantity": 1},
    {"product_id": "monitor-004", "quantity": 1},
    {"product_id": "headphones-005", "quantity": 1},
]

class TrafficGenerator:
    def __init__(self):
        self.created_users: List[str] = []
        self.created_orders: List[str] = []
        self.session = requests.Session()
        
    def generate_correlation_id(self) -> str:
        """Generate a unique correlation ID for request tracing."""
        return str(uuid.uuid4())
    
    def create_headers(self, correlation_id: str = None) -> Dict[str, str]:
        """Create headers with correlation ID for distributed tracing."""
        if not correlation_id:
            correlation_id = self.generate_correlation_id()
        
        return {
            "Content-Type": "application/json",
            "x-correlation-id": correlation_id,
            "x-request-id": str(uuid.uuid4()),
            "User-Agent": "TrafficGenerator/1.0"
        }
    
    def create_user(self, user_data: Dict[str, str]) -> str:
        """Create a user and return the user ID."""
        correlation_id = self.generate_correlation_id()
        headers = self.create_headers(correlation_id)
        
        print(f"🔵 Creating user: {user_data['name']} (correlation_id: {correlation_id})")
        
        try:
            response = self.session.post(
                f"{USER_SERVICE}/api/v1/users",
                json=user_data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            user_id = response.json()["id"]
            self.created_users.append(user_id)
            print(f"✅ User created: {user_id}")
            return user_id
            
        except Exception as e:
            print(f"❌ Failed to create user: {e}")
            return None
    
    def create_order(self, user_id: str, items: List[Dict[str, Any]]) -> str:
        """Create an order that flows through all services."""
        correlation_id = self.generate_correlation_id()
        headers = self.create_headers(correlation_id)
        
        order_data = {
            "user_id": user_id,
            "items": items
        }
        
        print(f"🟡 Creating order for user {user_id} (correlation_id: {correlation_id})")
        print(f"   Items: {items}")
        
        try:
            # This will trigger: user-service → order-service → inventory-service
            response = self.session.post(
                f"{USER_SERVICE}/api/v1/users/{user_id}/orders",
                json=order_data,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
            
            order_id = response.json().get("order_id", response.json().get("id", "unknown"))
            self.created_orders.append(order_id)
            print(f"✅ Order created: {order_id}")
            return order_id
            
        except Exception as e:
            print(f"❌ Failed to create order: {e}")
            return None
    
    def get_user_orders(self, user_id: str) -> List[Dict]:
        """Get user orders to generate read traces."""
        correlation_id = self.generate_correlation_id()
        headers = self.create_headers(correlation_id)
        
        print(f"🟢 Getting orders for user {user_id} (correlation_id: {correlation_id})")
        
        try:
            response = self.session.get(
                f"{USER_SERVICE}/api/v1/users/{user_id}/orders",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            orders = response.json()["orders"]
            print(f"✅ Retrieved {len(orders)} orders for user {user_id}")
            return orders
            
        except Exception as e:
            print(f"❌ Failed to get user orders: {e}")
            return []
    
    def check_inventory_direct(self, product_id: str) -> Dict:
        """Direct call to inventory service for comparison."""
        correlation_id = self.generate_correlation_id()
        headers = self.create_headers(correlation_id)
        
        print(f"🟣 Checking inventory for {product_id} (correlation_id: {correlation_id})")
        
        try:
            response = self.session.get(
                f"{INVENTORY_SERVICE}/api/v1/inventory/{product_id}",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            inventory = response.json()
            print(f"✅ Inventory check: {product_id} has {inventory.get('available_quantity', 0)} units")
            return inventory
            
        except Exception as e:
            print(f"❌ Failed to check inventory: {e}")
            return {}
    
    def get_all_inventory(self) -> List[Dict]:
        """Get all inventory items."""
        correlation_id = self.generate_correlation_id()
        headers = self.create_headers(correlation_id)
        
        print(f"🟣 Getting all inventory (correlation_id: {correlation_id})")
        
        try:
            response = self.session.get(
                f"{INVENTORY_SERVICE}/api/v1/inventory",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            inventory = response.json()["inventory"]
            print(f"✅ Retrieved {len(inventory)} inventory items")
            return inventory
            
        except Exception as e:
            print(f"❌ Failed to get inventory: {e}")
            return []
    
    def run_traffic_scenario(self, duration_seconds: int = 60):
        """Run a realistic traffic scenario for the specified duration."""
        print(f"🚀 Starting traffic generation for {duration_seconds} seconds...")
        print("=" * 60)
        
        start_time = time.time()
        
        # Phase 1: Create users
        print("\n📝 Phase 1: Creating users...")
        for user_data in SAMPLE_USERS:
            self.create_user(user_data)
            time.sleep(random.uniform(0.5, 2.0))  # Realistic delay
        
        # Phase 2: Generate orders and queries
        print("\n📦 Phase 2: Generating orders and queries...")
        
        while time.time() - start_time < duration_seconds:
            if self.created_users:
                # Random actions
                action = random.choice([
                    "create_order",
                    "get_user_orders", 
                    "check_inventory",
                    "get_all_inventory"
                ])
                
                if action == "create_order":
                    user_id = random.choice(self.created_users)
                    items = random.sample(SAMPLE_PRODUCTS, random.randint(1, 3))
                    self.create_order(user_id, items)
                
                elif action == "get_user_orders":
                    user_id = random.choice(self.created_users)
                    self.get_user_orders(user_id)
                
                elif action == "check_inventory":
                    product = random.choice(SAMPLE_PRODUCTS)
                    self.check_inventory_direct(product["product_id"])
                
                elif action == "get_all_inventory":
                    self.get_all_inventory()
                
                # Random delay between requests
                time.sleep(random.uniform(1.0, 3.0))
        
        print("\n" + "=" * 60)
        print(f"✅ Traffic generation completed!")
        print(f"📊 Summary:")
        print(f"   - Users created: {len(self.created_users)}")
        print(f"   - Orders created: {len(self.created_orders)}")
        print(f"   - Duration: {duration_seconds} seconds")
        print(f"\n🔍 Check SigNoz at http://localhost:8080 for distributed traces!")

def main():
    """Main function to run traffic generation."""
    generator = TrafficGenerator()
    
    # Run for 2 minutes by default
    duration = 120
    
    try:
        generator.run_traffic_scenario(duration)
    except KeyboardInterrupt:
        print("\n⏹️  Traffic generation stopped by user")
    except Exception as e:
        print(f"\n❌ Error during traffic generation: {e}")

if __name__ == "__main__":
    main()
