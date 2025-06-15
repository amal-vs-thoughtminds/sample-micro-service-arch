# Microservice Communication Library

A secure, maintainable library for microservice-to-microservice communication. Provides encryption, service discovery, and robust error handling.

## Features

- 🔒 **Secure Communication**: Automatic encryption/decryption of service-to-service communication
- 🔄 **Service Discovery**: Built-in service registry for managing microservice endpoints
- ⚡ **Robust Error Handling**: Automatic retries, circuit breaking, and comprehensive error handling
- 🛡️ **Middleware Support**: ASGI middleware for automatic request/response encryption
- 📝 **Type Safety**: Full type hints and validation using Pydantic
- 🔍 **Logging**: Comprehensive logging for debugging and monitoring
- 🧪 **Testing**: Built-in support for testing with pytest

## Installation

```bash
# Install from local directory
pip install -e ./shared

# Install with development dependencies
pip install -e ./shared[dev]
```

## Quick Start

1. Initialize the service registry:
```python
from ms_communicator import initialize_registry

initialize_registry()
```

2. Create a service client:
```python
from ms_communicator import MicroServiceClient

# Initialize client for your service
client = MicroServiceClient("your-service-name")

# Make a request to another service
response = await client.request(
    target_service="other-service",
    endpoint="/api/v1/endpoint",
    method="POST",
    payload={"key": "value"}
)
```

3. Add encryption middleware to your FastAPI app:
```python
from fastapi import FastAPI
from ms_communicator import EncryptionMiddleware

app = FastAPI()
app.add_middleware(
    EncryptionMiddleware,
    service_name="your-service-name",
    encrypt_responses=True
)
```

## Environment Variables

Required environment variables for each service:
```env
# Service-specific encryption keys
YOUR_SERVICE_ENCRYPTION_KEY=your-secret-key
OTHER_SERVICE_ENCRYPTION_KEY=other-service-key

# Service configuration
SERVICE_NAME=your-service-name
SERVICE_URL=http://your-service:8000
```

## Development

1. Install development dependencies:
```bash
pip install -e ./shared[dev]
```

2. Run tests:
```bash
pytest
```

3. Run linting:
```bash
flake8
black .
isort .
mypy .
```

## Architecture

### Components

1. **MicroServiceClient**: Main client for service-to-service communication
   - Handles encryption/decryption
   - Manages retries and circuit breaking
   - Service discovery

2. **EncryptionMiddleware**: ASGI middleware for automatic encryption
   - Encrypts responses when requests are encrypted
   - Handles encryption headers
   - Service identification

3. **Service Registry**: Manages service endpoints and health checks
   - Service registration
   - Health monitoring
   - Endpoint management

### Communication Flow

1. Service A makes a request:
   ```python
   # Service A encrypts with its key
   encrypted_data = service_a_key.encrypt(payload)
   headers = {
       "X-Encrypted-Payload": "true",
       "X-Encryption-Service": "service-a"
   }
   ```

2. Service B receives:
   ```python
   # Middleware detects encrypted request
   # Dependencies decrypt using Service A's key
   decrypted_data = service_a_key.decrypt(encrypted_data)
   ```

3. Service B responds:
   ```python
   # Middleware encrypts response with Service B's key
   encrypted_response = service_b_key.encrypt(response_data)
   headers = {
       "X-Encrypted-Payload": "true",
       "X-Encryption-Service": "service-b"
   }
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see LICENSE file for details
