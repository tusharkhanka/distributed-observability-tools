import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
import httpx
import logging

# Import distributed observability tools
from distributed_observability import TracingConfig, setup_tracing
from distributed_observability.utils import instrument_httpx_client

# Service identification
SERVICE_NAME = "order-service"
SERVICE_PORT = 9002

# Configure standard Python logging (tracing middleware handles structured logs)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Pydantic models
class Order(BaseModel):
    id: int
    user_id: int
    product_name: str
    quantity: int
    total_price: float
    status: str

class OrderCreate(BaseModel):
    user_id: int
    product_name: str
    quantity: int

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    quantity: Optional[int] = None

# In-memory storage for demo
orders_db = [
    Order(id=1, user_id=1, product_name="Laptop", quantity=1, total_price=999.99, status="completed"),
    Order(id=2, user_id=1, product_name="Mouse", quantity=2, total_price=59.98, status="completed"),
    Order(id=3, user_id=2, product_name="Keyboard", quantity=1, total_price=79.99, status="pending")
]



def create_app():
    app = FastAPI(
        title="Order Service",
        version="1.0.0",
        description="Order management service"
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

    # Instrument FastAPI app for auto-tracing
    from distributed_observability.tracing.tracer import instrument_fastapi_app
    instrument_fastapi_app(app, config)

    # Add middleware (pass the class and parameters, not the instance)
    from distributed_observability.framework.fastapi import RequestTracingMiddleware
    app.add_middleware(RequestTracingMiddleware, tracing_config=config)

    logger.info(f"🚀 Starting {SERVICE_NAME} with distributed-observability-tools")
    logger.info(f"📊 Tracing configured for SigNoz compatibility")
    logger.info(f"🎯 Correlation ID tracking enabled")

    otel_success = tracer_manager.is_ready()

    # Instrument httpx for automatic correlation propagation
    instrument_httpx_client()

    # Get inventory service URL from environment
    INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory-service:9003")

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
            "inventory_service_url": INVENTORY_SERVICE_URL,
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
    @app.get("/order-service/health")
    async def health_with_prefix(request: Request):
        return await health(request)

    @app.get("/api/v1/orders", response_model=List[Order])
    async def get_orders():
        """Get all orders"""
        logger.info("Getting all orders")
        return orders_db

    @app.get("/api/v1/orders/{order_id}", response_model=Order)
    async def get_order(order_id: int):
        """Get specific order by ID"""
        logger.info(f"Getting order {order_id}")
        order = next((o for o in orders_db if o.id == order_id), None)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order

    @app.get("/api/v1/orders/user/{user_id}", response_model=List[Order])
    async def get_orders_by_user(user_id: int):
        """Get all orders for a specific user"""
        logger.info(f"Getting orders for user {user_id}")
        user_orders = [o for o in orders_db if o.user_id == user_id]
        return user_orders

    @app.post("/api/v1/orders", response_model=Order)
    async def create_order(order: OrderCreate, request: Request):
        """Create new order with inventory check"""
        logger.info(f"Creating order for user {order.user_id}: {order.quantity}x {order.product_name}")

        # Extract correlation ID and other CloudFront headers to propagate
        incoming_headers = dict(request.headers)
        headers_to_propagate = {
            'x-correlation-id': incoming_headers.get('x-correlation-id'),
            'x-edge-location': incoming_headers.get('x-edge-location'),
            'x-request-id': incoming_headers.get('x-request-id'),
            'x-amz-cf-id': incoming_headers.get('x-amz-cf-id')
        }
        # Remove None values (headers that weren't present)
        headers_to_propagate = {k: v for k, v in headers_to_propagate.items() if v is not None}

        logger.info(f"Propagating correlation headers to inventory: {headers_to_propagate}")

        try:
            # Check inventory availability with propagated headers
            async with httpx.AsyncClient() as client:
                inventory_response = await client.get(
                    f"{INVENTORY_SERVICE_URL}/api/v1/inventory/product/{order.product_name}",
                    headers=headers_to_propagate
                )

                if inventory_response.status_code == 404:
                    raise HTTPException(status_code=404, detail="Product not found in inventory")

                inventory_response.raise_for_status()
                inventory_item = inventory_response.json()

                logger.info(f"Found inventory item: {inventory_item}")

                # Check if enough quantity available
                if inventory_item["quantity"] < order.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient inventory. Available: {inventory_item['quantity']}, Requested: {order.quantity}"
                    )

                # Reserve inventory with propagated headers
                reserve_response = await client.post(
                    f"{INVENTORY_SERVICE_URL}/api/v1/inventory/{inventory_item['id']}/reserve",
                    params={"quantity": order.quantity},
                    headers=headers_to_propagate
                )
                reserve_response.raise_for_status()

                # Calculate total price
                total_price = inventory_item["price"] * order.quantity

                # Create order
                new_id = max([o.id for o in orders_db], default=0) + 1
                new_order = Order(
                    id=new_id,
                    user_id=order.user_id,
                    product_name=order.product_name,
                    quantity=order.quantity,
                    total_price=total_price,
                    status="confirmed"
                )

                orders_db.append(new_order)
                logger.info(f"Created order with ID: {new_id}")

                return new_order

        except httpx.RequestError as e:
            logger.error(f"Error communicating with inventory service: {e}")
            raise HTTPException(status_code=503, detail="Inventory service unavailable")
        except httpx.HTTPStatusError as e:
            logger.error(f"Inventory service returned error: {e.response.status_code}")
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail="Product not found")
            elif e.response.status_code == 400:
                error_detail = e.response.json().get("detail", "Bad request to inventory service")
                raise HTTPException(status_code=400, detail=error_detail)
            else:
                raise HTTPException(status_code=503, detail="Inventory service error")

    @app.put("/api/v1/orders/{order_id}", response_model=Order)
    async def update_order(order_id: int, update: OrderUpdate):
        """Update order"""
        logger.info(f"Updating order {order_id}")
        
        order = next((o for o in orders_db if o.id == order_id), None)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if update.status is not None:
            order.status = update.status
        if update.quantity is not None:
            order.quantity = update.quantity
        
        logger.info(f"Updated order {order_id}")
        return order

    @app.delete("/api/v1/orders/{order_id}")
    async def delete_order(order_id: int):
        """Delete order"""
        logger.info(f"Deleting order {order_id}")
        
        order = next((o for o in orders_db if o.id == order_id), None)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        orders_db.remove(order)
        logger.info(f"Deleted order {order_id}")
        return {"message": "Order deleted successfully"}

    # ALB path routing - duplicate API endpoints with service prefix
    @app.get("/order-service/api/v1/orders", response_model=List[Order])
    async def get_orders_prefixed():
        return await get_orders()

    @app.get("/order-service/api/v1/orders/{order_id}", response_model=Order)
    async def get_order_prefixed(order_id: int):
        return await get_order(order_id)

    @app.get("/order-service/api/v1/orders/user/{user_id}", response_model=List[Order])
    async def get_orders_by_user_prefixed(user_id: int):
        return await get_orders_by_user(user_id)

    @app.post("/order-service/api/v1/orders", response_model=Order)
    async def create_order_prefixed(order: OrderCreate):
        return await create_order(order)

    @app.put("/order-service/api/v1/orders/{order_id}", response_model=Order)
    async def update_order_prefixed(order_id: int, update: OrderUpdate):
        return await update_order(order_id, update)

    @app.delete("/order-service/api/v1/orders/{order_id}")
    async def delete_order_prefixed(order_id: int):
        return await delete_order(order_id)

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9002)
