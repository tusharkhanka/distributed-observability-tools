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
SERVICE_NAME = "user-service"
SERVICE_PORT = 9001

# Configure standard Python logging (tracing middleware handles structured logs)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Pydantic models
class User(BaseModel):
    id: int
    name: str
    email: str
    status: str

class UserCreate(BaseModel):
    name: str
    email: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None

# In-memory storage for demo
users_db = [
    User(id=1, name="John Doe", email="john@example.com", status="active"),
    User(id=2, name="Jane Smith", email="jane@example.com", status="active"),
    User(id=3, name="Bob Johnson", email="bob@example.com", status="inactive")
]



def create_app():
    app = FastAPI(
        title="User Service",
        version="1.0.0",
        description="User management service"
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

    # Add middleware (pass the class and parameters, not the instance)
    from distributed_observability.framework.fastapi import RequestTracingMiddleware
    app.add_middleware(RequestTracingMiddleware, tracing_config=config)

    logger.info(f"🚀 Starting {SERVICE_NAME} with distributed-observability-tools")
    logger.info(f"📊 Tracing configured for SigNoz compatibility")
    logger.info(f"🎯 Correlation ID tracking enabled")

    otel_success = tracer_manager.is_ready()

    # Instrument httpx for automatic correlation propagation
    instrument_httpx_client()

    # Get order service URL from environment
    ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:9002")

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
            "order_service_url": ORDER_SERVICE_URL,
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
    @app.get("/user-service/health")
    async def health_with_prefix(request: Request):
        return await health(request)

    @app.get("/api/v1/users", response_model=List[User])
    async def get_users():
        """Get all users"""
        logger.info("Getting all users")
        return users_db

    @app.get("/api/v1/users/{user_id}", response_model=User)
    async def get_user(user_id: int):
        """Get specific user by ID"""
        logger.info(f"Getting user {user_id}")
        user = next((u for u in users_db if u.id == user_id), None)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    @app.post("/api/v1/users", response_model=User)
    async def create_user(user: UserCreate):
        """Create new user"""
        logger.info(f"Creating user: {user.name}")
        
        # Check if email already exists
        existing = next((u for u in users_db if u.email == user.email), None)
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        
        new_id = max([u.id for u in users_db], default=0) + 1
        new_user = User(id=new_id, name=user.name, email=user.email, status="active")
        users_db.append(new_user)
        
        logger.info(f"Created user with ID: {new_id}")
        return new_user

    @app.put("/api/v1/users/{user_id}", response_model=User)
    async def update_user(user_id: int, update: UserUpdate):
        """Update user"""
        logger.info(f"Updating user {user_id}")
        
        user = next((u for u in users_db if u.id == user_id), None)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if update.name is not None:
            user.name = update.name
        if update.email is not None:
            user.email = update.email
        if update.status is not None:
            user.status = update.status
        
        logger.info(f"Updated user {user_id}")
        return user

    @app.delete("/api/v1/users/{user_id}")
    async def delete_user(user_id: int):
        """Delete user"""
        logger.info(f"Deleting user {user_id}")
        
        user = next((u for u in users_db if u.id == user_id), None)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        users_db.remove(user)
        logger.info(f"Deleted user {user_id}")
        return {"message": "User deleted successfully"}

    @app.get("/api/v1/users/{user_id}/orders")
    async def get_user_orders(user_id: int, request: Request):
        """Get all orders for a specific user (calls order service)"""
        logger.info(f"Getting orders for user {user_id}")

        # First check if user exists
        user = next((u for u in users_db if u.id == user_id), None)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Correlation headers are now automatically propagated by the instrumentation!
        logger.info(f"📊 Correlation headers automatically propagated via instrumentation")

        try:
            # Call order service - correlation headers added automatically by instrument_httpx_client()
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{ORDER_SERVICE_URL}/api/v1/orders/user/{user_id}")
                response.raise_for_status()
                orders = response.json()

                logger.info(f"Found {len(orders)} orders for user {user_id}")

                return {
                    "user": user,
                    "orders": orders,
                    "total_orders": len(orders)
                }

        except httpx.RequestError as e:
            logger.error(f"Error communicating with order service: {e}")
            raise HTTPException(status_code=503, detail="Order service unavailable")
        except httpx.HTTPStatusError as e:
            logger.error(f"Order service returned error: {e.response.status_code}")
            raise HTTPException(status_code=503, detail="Order service error")

    @app.post("/api/v1/users/{user_id}/orders")
    async def create_user_order(user_id: int, order_data: dict, request: Request):
        """Create an order for a user (calls order service)"""
        logger.info(f"Creating order for user {user_id}")

        # First check if user exists
        user = next((u for u in users_db if u.id == user_id), None)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

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

        logger.info(f"Propagating correlation headers: {headers_to_propagate}")

        try:
            # Add user_id to order data
            order_data["user_id"] = user_id

            # Call order service to create order with propagated headers
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{ORDER_SERVICE_URL}/api/v1/orders",
                    json=order_data,
                    headers=headers_to_propagate
                )
                response.raise_for_status()
                order = response.json()

                logger.info(f"Created order {order['id']} for user {user_id}")

                return {
                    "message": "Order created successfully",
                    "user": user,
                    "order": order
                }

        except httpx.RequestError as e:
            logger.error(f"Error communicating with order service: {e}")
            raise HTTPException(status_code=503, detail="Order service unavailable")
        except httpx.HTTPStatusError as e:
            logger.error(f"Order service returned error: {e.response.status_code}")
            error_detail = "Order creation failed"
            try:
                error_response = e.response.json()
                error_detail = error_response.get("detail", error_detail)
            except:
                pass
            raise HTTPException(status_code=e.response.status_code, detail=error_detail)

    # ALB path routing - duplicate API endpoints with service prefix
    @app.get("/user-service/api/v1/users", response_model=List[User])
    async def get_users_prefixed():
        return await get_users()

    @app.get("/user-service/api/v1/users/{user_id}", response_model=User)
    async def get_user_prefixed(user_id: int):
        return await get_user(user_id)

    @app.post("/user-service/api/v1/users", response_model=User)
    async def create_user_prefixed(user: UserCreate):
        return await create_user(user)

    @app.put("/user-service/api/v1/users/{user_id}", response_model=User)
    async def update_user_prefixed(user_id: int, update: UserUpdate):
        return await update_user(user_id, update)

    @app.delete("/user-service/api/v1/users/{user_id}")
    async def delete_user_prefixed(user_id: int):
        return await delete_user(user_id)

    @app.get("/user-service/api/v1/users/{user_id}/orders")
    async def get_user_orders_prefixed(user_id: int):
        return await get_user_orders(user_id)

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001)
