# Docker-Only Microservices POC

A simplified microservices proof-of-concept that runs entirely in Docker containers with OpenTelemetry distributed tracing.

## 📋 Prerequisites

### Required Software
- **Docker** (version 20.10+) with Docker Compose
- **OpenTelemetry Collector binary** running on host machine at port 4317

### Check Prerequisites

```bash
# Verify Docker is installed and running
docker --version
docker-compose --version
docker info

# Verify OTel Collector is running on host
curl -v http://localhost:4317
# Should connect successfully (may return error response, but connection should work)
```

### Install OTel Collector Binary

If you don't have OTel Collector running, install it on your host machine:

```bash
# Download and install OTel Collector binary
# Follow instructions at: https://opentelemetry.io/docs/collector/installation/

# Example for Linux/macOS:
curl -L -o otelcol https://github.com/open-telemetry/opentelemetry-collector-releases/releases/latest/download/otelcol_linux_amd64
chmod +x otelcol

# Start collector (basic configuration)
./otelcol --config=config.yaml
```

## 🚀 Quick Start

### 1. Clone/Download the Project

```bash
# Navigate to the POC directory
cd POC-docker-only
```

### 2. Start Docker Desktop

**Make sure Docker is running:**
- On macOS/Windows: Start Docker Desktop application
- On Linux: `sudo systemctl start docker`

### 3. Single Command Startup

**Option 1 - Automated troubleshooting (Recommended):**
```bash
./troubleshoot.sh
```

**Option 2 - Direct startup:**
```bash
# Use docker-compose if available, otherwise docker compose
docker-compose up
# OR
docker compose up
```

**To run in background (detached mode):**

```bash
docker-compose up -d
# OR
docker compose up -d
```

### 4. Verify Services are Running

Wait about 60-90 seconds for all services to build and start, then check:

```bash
# Check all containers are running
docker-compose ps
# OR
docker compose ps

# Should show 3 services running and healthy
```

**If you see "unhealthy" status, wait longer or run the troubleshoot script:**
```bash
./troubleshoot.sh
```

## 🔍 Service Verification

### Health Checks

Test each service health endpoint:

```bash
# User Service (Port 9001)
curl http://localhost:9001/health

# Order Service (Port 9002)
curl http://localhost:9002/health

# Inventory Service (Port 9003)
curl http://localhost:9003/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "user-service",
  "port": 9001,
  "otel_enabled": true,
  "order_service_url": "http://order-service:9002"
}
```

## 🧪 API Testing Examples

### User Service (Port 9001)

```bash
# Get all users
curl http://localhost:9001/api/v1/users

# Get specific user
curl http://localhost:9001/api/v1/users/1

# Create new user
curl -X POST http://localhost:9001/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "email": "test@example.com"}'

# Get user orders (calls order-service)
curl http://localhost:9001/api/v1/users/1/orders

# Create order for user (calls order-service → inventory-service)
curl -X POST http://localhost:9001/api/v1/users/1/orders \
  -H "Content-Type: application/json" \
  -d '{"product_name": "Mouse", "quantity": 1}'
```

### Order Service (Port 9002)

```bash
# Get all orders
curl http://localhost:9002/api/v1/orders

# Get specific order
curl http://localhost:9002/api/v1/orders/1

# Get orders for a user
curl http://localhost:9002/api/v1/orders/user/1

# Create new order (calls inventory-service)
curl -X POST http://localhost:9002/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "product_name": "Keyboard", "quantity": 1}'
```

### Inventory Service (Port 9003)

```bash
# Get all inventory
curl http://localhost:9003/api/v1/inventory

# Get specific inventory item
curl http://localhost:9003/api/v1/inventory/1

# Get inventory by product name
curl http://localhost:9003/api/v1/inventory/product/Laptop

# Create new inventory item
curl -X POST http://localhost:9003/api/v1/inventory \
  -H "Content-Type: application/json" \
  -d '{"product_name": "Webcam", "quantity": 20, "price": 89.99}'

# Reserve inventory (used by order service)
curl -X POST http://localhost:9003/api/v1/inventory/1/reserve?quantity=1
```

## 🔗 Cross-Service Communication Flow

The services demonstrate distributed tracing through cross-service calls:

1. **User → Order → Inventory**: When you create an order via user service
2. **Order → Inventory**: When you create an order directly via order service
3. **User → Order**: When you get user orders

### Test Complete Cross-Service Flow

```bash
# This creates a trace across all three services:
# user-service → order-service → inventory-service
curl -X POST http://localhost:9001/api/v1/users/1/orders \
  -H "Content-Type: application/json" \
  -d '{"product_name": "Laptop", "quantity": 1}'
```

## 🛠️ Management Commands

### View Logs

```bash
# View logs from all services
docker-compose logs

# View logs from specific service
docker-compose logs user-service
docker-compose logs order-service
docker-compose logs inventory-service

# Follow logs in real-time
docker-compose logs -f

# View logs with timestamps
docker-compose logs -t
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop and remove images
docker-compose down --rmi all
```

### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart user-service
```

### Rebuild Services

```bash
# Rebuild and restart (after code changes)
docker-compose up --build

# Rebuild specific service
docker-compose build user-service
docker-compose up -d user-service
```

## 🔧 Configuration

### Environment Variables

The services use these environment variables (configured in docker-compose.yml):

- `ORDER_SERVICE_URL` - URL for order service communication
- `INVENTORY_SERVICE_URL` - URL for inventory service communication
- `OTEL_EXPORTER_OTLP_ENDPOINT` - OpenTelemetry collector endpoint
- `OTEL_EXPORTER_OTLP_PROTOCOL` - Protocol for OTel communication (grpc)
- `OTEL_SERVICE_NAME` - Service name for tracing

### Port Configuration

- **User Service**: `localhost:9001`
- **Order Service**: `localhost:9002`
- **Inventory Service**: `localhost:9003`

### Docker Networking

- **Internal communication**: Services use Docker service names (e.g., `http://order-service:9002`)
- **External OTel Collector**: Uses `host.docker.internal:4317` to reach host machine
- **Network**: Custom bridge network `poc-docker-network`

## 🐛 Troubleshooting

### Services Won't Start

**Check Docker:**
```bash
# Verify Docker is running
docker info

# Check for port conflicts
netstat -an | grep 900

# View detailed logs
docker-compose logs
```

**Build Issues:**
```bash
# Clean rebuild
docker-compose down --rmi all
docker-compose build --no-cache
docker-compose up
```

### Service Communication Issues

**Check Internal Networking:**
```bash
# Test service-to-service communication
docker-compose exec user-service curl http://order-service:9002/health
docker-compose exec order-service curl http://inventory-service:9003/health

# Check network connectivity
docker network ls
docker network inspect poc-docker-network
```

**Check Service Health:**
```bash
# Individual service health checks
curl http://localhost:9001/health
curl http://localhost:9002/health
curl http://localhost:9003/health
```

### OpenTelemetry Issues

**OTel Collector Not Reachable:**
```bash
# Check if collector is running on host
curl -v http://localhost:4317

# Check from inside container
docker-compose exec user-service curl -v http://host.docker.internal:4317
```

**No Traces Appearing:**
1. Verify OTel Collector is running and configured correctly
2. Check service logs for OTel errors:
   ```bash
   docker-compose logs user-service | grep -i otel
   ```
3. Services will continue working even if OTel fails (graceful degradation)

**Docker Host Networking Issues:**
- On Linux: OTel Collector should be accessible at `host.docker.internal:4317`
- On older Docker versions: Try `172.17.0.1:4317` instead
- On Windows/macOS: `host.docker.internal` should work automatically

### Performance Issues

**Slow Startup:**
```bash
# Services have health checks and dependencies
# Wait 60-90 seconds for complete startup
docker-compose ps

# Check startup order: inventory → order → user
```

**Memory Issues:**
```bash
# Check container resource usage
docker stats

# Increase Docker memory limits if needed
```

### Reset Everything

```bash
# Complete cleanup and restart
docker-compose down -v --rmi all
docker system prune -f
docker-compose up --build
```

## 📊 Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Service  │    │  Order Service  │    │Inventory Service│
│   Port: 9001    │◄──►│   Port: 9002    │◄──►│   Port: 9003    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ OTel Collector  │
                    │ Host:4317       │
                    └─────────────────┘
```

### Features

- ✅ **Docker containerization** with multi-stage builds
- ✅ **Cross-service communication** with HTTP calls
- ✅ **OpenTelemetry distributed tracing** to external collector
- ✅ **Health checks** for service monitoring
- ✅ **Dependency management** with proper startup order
- ✅ **Graceful error handling** and fallback mechanisms
- ✅ **No local Python dependencies** required

## 🎯 Success Criteria

When everything is working correctly:

1. ✅ All three services respond to health checks
2. ✅ Each service serves its API endpoints
3. ✅ Cross-service calls work (user→order→inventory)
4. ✅ Services accessible on localhost ports 9001, 9002, 9003
5. ✅ OpenTelemetry traces sent to external collector
6. ✅ Docker containers running without errors
7. ✅ Services start in correct dependency order

## 📚 API Documentation

Once services are running, access interactive API documentation:

- **User Service**: http://localhost:9001/docs
- **Order Service**: http://localhost:9002/docs
- **Inventory Service**: http://localhost:9003/docs

## 🔄 Development Workflow

### Making Code Changes

1. **Edit service code** in respective directories
2. **Rebuild specific service**:
   ```bash
   docker-compose build user-service
   docker-compose up -d user-service
   ```
3. **Test changes**:
   ```bash
   curl http://localhost:9001/health
   ```

### Adding New Dependencies

1. **Update requirements.txt** in service directory
2. **Rebuild container**:
   ```bash
   docker-compose build --no-cache user-service
   ```

---

**🎉 You're all set!** The Docker-only microservices POC is ready for testing with full OpenTelemetry distributed tracing.
