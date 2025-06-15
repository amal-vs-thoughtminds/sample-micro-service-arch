# Sample FastAPI Microservices Architecture

A sample microservices architecture built with FastAPI, featuring encrypted inter-service communication, async database operations, comprehensive logging, and auto-reload development environment.

## Architecture Overview

### Services
- **User Service** (Port 8002): User management, authentication, JWT tokens
- **Analytics Service** (Port 8001): Event tracking, analytics data, statistics

### Databases
- **PostgreSQL**: Primary database with async SQLAlchemy ORM
- **MongoDB**: Document storage with async Motor driver

### Key Features
- **Async/Await**: Full async SQLAlchemy with AsyncSession
- **Enhanced Dispatcher**: Retry logic, exponential backoff, connection pooling
- **Comprehensive Logging**: All log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Hot Reload**: Automatic code reload in development
- **Production Ready**: Gunicorn with multiple workers for production
- **Health Checks**: Docker health checks and service monitoring
- **Encrypted Communication**: AES-256 encryption between services
- **Optional Encryption**: Flexible encryption based on endpoint needs
- **Decoupled Services**: Each function in separate files
- **Selective Migrations**: Control which models use Alembic
- **MongoDB Singleton**: Efficient connection management

## Quick Start

### Development Environment (Hot Reload)
```bash
# Start all services with hot reload
docker-compose up --build

# View logs
docker-compose logs -f user-service
docker-compose logs -f analytics-service

# Health checks
curl http://localhost:8002/health  # User Service
curl http://localhost:8001/health  # Analytics Service
```

### Production Environment (Gunicorn)
```bash
# Start production environment
docker-compose -f docker-compose.prod.yml up --build -d

# Scale services
docker-compose -f docker-compose.prod.yml up --scale user-service=3 --scale analytics-service=2
```

## Project Structure

```
├── user/                           # User microservice
│   ├── app/
│   │   ├── api/user/              # API layer
│   │   │   ├── routes.py          # FastAPI routes
│   │   │   ├── schemas.py         # Pydantic models
│   │   │   └── services/          # Decoupled business logic
│   │   │       ├── create_user.py     # Individual service functions
│   │   │       ├── authenticate_user.py
│   │   │       └── get_user_stats.py
│   │   ├── models/                # Common models location
│   │   │   └── user.py           # PostgreSQL models
│   │   ├── core/                  # Core configuration
│   │   │   ├── config.py         # Settings
│   │   │   ├── db.py             # Async SQLAlchemy setup
│   │   │   ├── dependencies.py   # FastAPI dependencies
│   │   │   ├── dispatcher.py     # Enhanced inter-service communication
│   │   │   ├── encryption.py     # AES-256 encryption
│   │   │   ├── jwt_handler.py    # JWT authentication
│   │   │   ├── middleware.py     # Custom middleware
│   │   │   └── mongodb.py        # MongoDB singleton
│   │   ├── utils/
│   │   │   └── logger.py         # Comprehensive logging
│   │   └── main.py               # FastAPI application
│   ├── logs/                     # Application logs
│   ├── Dockerfile                # Development Dockerfile
│   ├── Dockerfile.prod          # Production Dockerfile (Gunicorn)
│   ├── requirements.txt         # Python dependencies
│   └── .env                     # Environment variables
│
├── analytics/                    # Analytics microservice
│   └── [similar structure]
│
├── docker-compose.yml           # Development environment
├── docker-compose.prod.yml     # Production environment
└── README.md                   # This file
```

## Technical Doc

### 1. Async SQLAlchemy Implementation
- **AsyncSession**: All database operations use async/await
- **Connection Pooling**: Optimized database connections
- **Automatic Session Management**: Context managers handle session lifecycle

```python
async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    result = await db.execute(select(User).where(User.username == user_data.username))
    existing_user = result.scalar_one_or_none()
    # ...
    await db.commit()
    await db.refresh(db_user)
    return db_user
```

### 2. Enhanced Dispatcher
- **Retry Logic**: Exponential backoff for failed requests
- **Connection Pooling**: Reusable HTTP client connections
- **Error Handling**: Comprehensive error logging with timing
- **Dual Mode**: Encrypted and unencrypted communication

```python
async def send_encrypted_request(
    self, service: str, endpoint: str, data: Dict[str, Any], 
    method: str = "POST", timeout: Optional[float] = None
) -> Dict[str, Any]:
    
```

### 3. Comprehensive Logging
- **Multiple Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **File Rotation**: Automatic log file rotation (10MB max)
- **Colored Console**: Color-coded console output for development
- **Separate Error Logs**: Dedicated error log files
- **Third-party Library Logs**: Configured logging for SQLAlchemy, HTTPX, etc.

```python
# Logs created automatically:
logs/
├── user-service.log           # All logs
├── user-service_errors.log    # Errors only
├── analytics-service.log      # All logs
└── analytics-service_errors.log
```

### 4. Hot Reload Development
- **Volume Mounts**: Code changes reflect immediately
- **Debug Logging**: Detailed logs in development
- **Uvicorn Reload**: Automatic server restart on code changes

### 5. Production Configuration
- **Gunicorn**: Multiple worker processes
- **Resource Limits**: Memory and CPU constraints
- **Health Checks**: Docker health monitoring
- **Restart Policies**: Automatic container restart

## Security Features

### Encryption
- **AES-256**: Fernet encryption for inter-service communication
- **Optional Encryption**: Headers control encryption requirements
- **JWT Authentication**: Secure user authentication

### Headers
```
X-Service-Communication: encrypted     # Mandatory encryption
X-Encrypt-Response: true              # Optional encryption
```

## Database Configuration

### PostgreSQL (Async)
- **Async SQLAlchemy**: Full async/await support
- **Selective Migrations**: Control which models use Alembic
- **Connection Pooling**: Optimized connection management

### MongoDB (Singleton)
- **Motor Driver**: Async MongoDB operations
- **Singleton Pattern**: Single connection instance
- **Proper Lifecycle**: Clean connection management

## Docker Configuration

### Development
```bash
# Hot reload enabled, debug logging, volume mounts
docker-compose up
```

### Production
```bash
# Gunicorn workers, production logging, no volume mounts
docker-compose -f docker-compose.prod.yml up -d
```

## API Endpoints

### User Service (Port 8002)
```
POST /api/v1/users/register     # User registration (encrypted)
POST /api/v1/users/login        # User login (optional encryption)
GET  /api/v1/users/profile      # User profile (optional encryption)
GET  /api/v1/users/stats/count  # User count (public)
GET  /health                    # Health check
```

### Analytics Service (Port 8001)
```
POST /api/v1/analytics/events   # Create event (encrypted)
GET  /api/v1/analytics/stats    # Get stats (optional encryption)
GET  /health                    # Health check
```

## Environment Variables

### Development (.env)
```bash
LOG_LEVEL=DEBUG
PRODUCTION=false
POSTGRES_HOST=postgres
MONGODB_HOST=mongodb
```

### Production (.env)
```bash
LOG_LEVEL=INFO
PRODUCTION=true
POSTGRES_HOST=your-postgres-host
MONGODB_HOST=your-mongodb-host
```

## Deployment

### Development
```bash
# Start with hot reload
docker-compose up --build

# View specific service logs
docker-compose logs -f user-service

# Scale services
docker-compose up --scale user-service=2
```


## Monitoring & Logs

### Log Files
```bash
# View live logs
tail -f user/logs/user-service.log
tail -f analytics/logs/analytics-service.log

# Error logs only
tail -f user/logs/user-service_errors.log
```

### Health Monitoring
```bash
# Check service health
curl http://localhost:8002/health
curl http://localhost:8001/health

# Docker health status
docker ps  # Shows health status
```

## Development

### Adding New Services
1. Create service function in `services/` directory
2. Add route in `routes.py`
3. Define schemas in `schemas.py`
4. Update dependencies as needed

### Database Migrations
```bash
# Create migration
cd user
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

## Service Communication Examples

### Encrypted Communication
```python
# Analytics service calls user service
result = await dispatcher.call_user_service(
    "/api/v1/users/stats/count", 
    encrypted=False,  # Public endpoint
    method="GET"
)
```

### Optional Encryption
```python
# Client requests with optional encryption
headers = {"X-Encrypt-Response": "true"}
response = requests.post(url, headers=headers, json=data)
```

## Performance Features

- **Async/Await**: Non-blocking I/O operations
- **Connection Pooling**: Reused database and HTTP connections
- **Resource Limits**: Controlled memory and CPU usage
- **Health Checks**: Automatic failure detection
- **Retry Logic**: Automatic recovery from transient failures

This architecture provides a robust, scalable, and maintainable foundation for microservices development with modern Python async patterns. 

### Encrypted Communication Flow

User Service               Analytics Service
   |                           |
   |-- Encrypted Request -->   |
   |   (using USER_KEY)        |-- Decrypts using get_decrypted_payload
   |                           |-- Processes request
   |                           |-- Encrypts response using get_encryption_manager
   |<-- Encrypted Response --  |
   |   (using ANALYTICS_KEY)   |
