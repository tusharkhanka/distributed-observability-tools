import os
import sys
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
import logging

# Import distributed observability tools
from distributed_observability import TracingConfig, setup_tracing

# Service identification
SERVICE_NAME = "inventory-service"
SERVICE_PORT = 9003

# Configure structured JSON logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add structured JSON formatter if not already configured
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = StructuredJSONFormatter(SERVICE_NAME, SERVICE_PORT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)



# Pydantic models
class InventoryItem(BaseModel):
    id: int
    product_name: str
    quantity: int
    price: float

class InventoryCreate(BaseModel):
    product_name: str
    quantity: int
    price: float

class InventoryUpdate(BaseModel):
    quantity: Optional[int] = None
    price: Optional[float] = None

# In-memory storage for demo
inventory_db = [
    InventoryItem(id=1, product_name="Laptop", quantity=10, price=999.99),
    InventoryItem(id=2, product_name="Mouse", quantity=50, price=29.99),
    InventoryItem(id=3, product_name="Keyboard", quantity=25, price=79.99),
    InventoryItem(id=4, product_name="Monitor", quantity=15, price=299.99),
    InventoryItem(id=5, product_name="Webcam", quantity=30, price=89.99)
]



def create_app():
    app = FastAPI(
        title="Inventory Service",
        version="1.0.0",
        description="Inventory management service"
        # Removed root_path - we'll handle prefixes explicitly
    )

    # Configure distributed observability (5 lines instead of 50+!)
    config = TracingConfig(
        service_name=SERVICE_NAME,
        collector_url=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://host.docker.internal:4317"),
        service_version="1.0.0",
        environment=os.getenv("ENVIRONMENT", "development")
    )

    # Setup tracing with the package
    tracer_manager, middleware = setup_tracing(config)

    # Add middleware
    app.add_middleware(middleware)

    logger.info(f"🚀 Starting {SERVICE_NAME} with distributed-observability-tools")
    logger.info(f"📊 Tracing configured for SigNoz compatibility")
    logger.info(f"🎯 Correlation ID tracking enabled")

    otel_success = tracer_manager.is_ready()

    # Inventory service doesn't make outbound HTTP calls, so no instrumentation needed
    # instrument_httpx_client() would be called here if needed

    @app.get("/health")
    async def health(request: Request):
        # Extract correlation ID for health check logging
        correlation_id = request.headers.get('x-correlation-id', 'not-found')

        # Log health check with correlation tracking
        logger.info(f"🏥 HEALTH CHECK | Correlation ID: {correlation_id} | Service: {SERVICE_NAME}")

        return {
            "status": "healthy",
            "service": SERVICE_NAME,
            "port": SERVICE_PORT,
            "otel_enabled": otel_success,
            "enhanced_logging": True,
            "correlation_id": correlation_id,
            "debug_info": {
                "request_headers_count": len(request.headers),
                "lambda_edge_headers": {
                    "x_correlation_id": request.headers.get('x-correlation-id', 'not-found'),
                    "x_edge_location": request.headers.get('x-edge-location', 'not-found'),
                    "x_request_id": request.headers.get('x-request-id', 'not-found'),
                    "x_amz_cf_id": request.headers.get('x-amz-cf-id', 'not-found')
                }
            }
        }

    # ALB path routing - handle requests with service prefix
    @app.get("/inventory-service/health")
    async def health_with_prefix(request: Request):
        return await health(request)

    @app.get("/api/v1/inventory", response_model=List[InventoryItem])
    async def get_inventory():
        """Get all inventory items"""
        logger.info("Getting all inventory items")
        return inventory_db

    @app.get("/api/v1/inventory/{item_id}", response_model=InventoryItem)
    async def get_inventory_item(item_id: int):
        """Get specific inventory item by ID"""
        logger.info(f"Getting inventory item {item_id}")
        item = next((i for i in inventory_db if i.id == item_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        return item

    @app.get("/api/v1/inventory/product/{product_name}", response_model=InventoryItem)
    async def get_inventory_by_product(product_name: str):
        """Get inventory item by product name"""
        logger.info(f"Getting inventory for product: {product_name}")
        item = next((i for i in inventory_db if i.product_name.lower() == product_name.lower()), None)
        if not item:
            raise HTTPException(status_code=404, detail="Product not found in inventory")
        return item

    @app.post("/api/v1/inventory", response_model=InventoryItem)
    async def create_inventory_item(item: InventoryCreate):
        """Create new inventory item"""
        logger.info(f"Creating inventory item: {item.product_name}")
        
        # Check if product already exists
        existing = next((i for i in inventory_db if i.product_name.lower() == item.product_name.lower()), None)
        if existing:
            raise HTTPException(status_code=400, detail="Product already exists")
        
        new_id = max([i.id for i in inventory_db], default=0) + 1
        new_item = InventoryItem(id=new_id, **item.dict())
        inventory_db.append(new_item)
        
        logger.info(f"Created inventory item with ID: {new_id}")
        return new_item

    @app.put("/api/v1/inventory/{item_id}", response_model=InventoryItem)
    async def update_inventory_item(item_id: int, update: InventoryUpdate):
        """Update inventory item"""
        logger.info(f"Updating inventory item {item_id}")
        
        item = next((i for i in inventory_db if i.id == item_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        if update.quantity is not None:
            item.quantity = update.quantity
        if update.price is not None:
            item.price = update.price
        
        logger.info(f"Updated inventory item {item_id}")
        return item

    @app.delete("/api/v1/inventory/{item_id}")
    async def delete_inventory_item(item_id: int):
        """Delete inventory item"""
        logger.info(f"Deleting inventory item {item_id}")
        
        item = next((i for i in inventory_db if i.id == item_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        inventory_db.remove(item)
        logger.info(f"Deleted inventory item {item_id}")
        return {"message": "Item deleted successfully"}

    @app.post("/api/v1/inventory/{item_id}/reserve")
    async def reserve_inventory(item_id: int, quantity: int):
        """Reserve inventory for an order"""
        logger.info(f"Reserving {quantity} units of item {item_id}")
        
        item = next((i for i in inventory_db if i.id == item_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        if item.quantity < quantity:
            raise HTTPException(status_code=400, detail="Insufficient inventory")
        
        item.quantity -= quantity
        logger.info(f"Reserved {quantity} units of {item.product_name}")
        
        return {
            "message": "Inventory reserved successfully",
            "reserved_quantity": quantity,
            "remaining_quantity": item.quantity
        }

    # ALB path routing - duplicate API endpoints with service prefix
    @app.get("/inventory-service/api/v1/inventory", response_model=List[InventoryItem])
    async def get_inventory_prefixed():
        return await get_inventory()

    @app.get("/inventory-service/api/v1/inventory/{item_id}", response_model=InventoryItem)
    async def get_inventory_item_prefixed(item_id: int):
        return await get_inventory_item(item_id)

    @app.get("/inventory-service/api/v1/inventory/product/{product_name}", response_model=InventoryItem)
    async def get_inventory_by_product_prefixed(product_name: str):
        return await get_inventory_by_product(product_name)

    @app.post("/inventory-service/api/v1/inventory", response_model=InventoryItem)
    async def create_inventory_item_prefixed(item: InventoryCreate):
        return await create_inventory_item(item)

    @app.put("/inventory-service/api/v1/inventory/{item_id}", response_model=InventoryItem)
    async def update_inventory_item_prefixed(item_id: int, update: InventoryUpdate):
        return await update_inventory_item(item_id, update)

    @app.delete("/inventory-service/api/v1/inventory/{item_id}")
    async def delete_inventory_item_prefixed(item_id: int):
        return await delete_inventory_item(item_id)

    @app.post("/inventory-service/api/v1/inventory/{item_id}/reserve")
    async def reserve_inventory_prefixed(item_id: int, quantity: int):
        return await reserve_inventory(item_id, quantity)

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9003)
