# Architecture Documentation

## Overview

This connector follows **Clean Architecture** principles to ensure maintainability, testability, and independence from external frameworks.

## Architecture Layers

```
┌─────────────────────────────────────────────┐
│            API Layer (FastAPI)              │
│         REST endpoints, webhooks            │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         Application Layer                   │
│    Use Cases (Business Logic)               │
│  - SyncOrdersUseCase                        │
│  - SyncProductsUseCase                      │
│  - SyncStockUseCase                         │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│          Domain Layer                       │
│    Entities & Business Rules                │
│  - Order                                    │
│  - Product                                  │
│  - Value Objects                            │
└─────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│      Infrastructure Layer                   │
│   External Services & Frameworks            │
│  - WooCommerceClient (REST API)             │
│  - OdooClient (JSON-RPC)                    │
│  - Database (PostgreSQL)                    │
└─────────────────────────────────────────────┘
```

## Layer Responsibilities

### 1. API Layer (`api/`)

**Purpose**: Handle HTTP requests and responses

**Components**:
- `main.py`: FastAPI application setup
- `routes/sync.py`: Manual sync endpoints
- `routes/webhooks.py`: Webhook handlers

**Dependencies**: Application layer, Domain layer

### 2. Application Layer (`application/`)

**Purpose**: Implement business use cases

**Components**:
- `sync_orders.py`: Order synchronization logic
- `sync_products.py`: Product synchronization logic
- `sync_stock.py`: Stock synchronization logic

**Key Principles**:
- One use case per file
- Orchestrates domain models and infrastructure
- Contains no framework-specific code
- Easy to test in isolation

**Dependencies**: Domain layer, Infrastructure layer

### 3. Domain Layer (`domain/`)

**Purpose**: Core business entities and rules

**Components**:
- `order.py`: Order entity and value objects
- `product.py`: Product entity

**Key Principles**:
- Framework-independent
- Contains business rules and validations
- Conversion logic between external systems
- No dependencies on outer layers

**Dependencies**: None (pure Python)

### 4. Infrastructure Layer (`infrastructure/`)

**Purpose**: External integrations and technical concerns

**Components**:
- `woocommerce/client.py`: WooCommerce REST API client
- `odoo/client.py`: Odoo JSON-RPC client
- `persistence/`: Database repositories (optional)

**Key Principles**:
- Implements interfaces defined by application layer
- Handles external API communication
- Can be swapped without affecting business logic

**Dependencies**: External libraries (httpx, etc.)

## Data Flow

### Example: Syncing an Order

```
1. HTTP Request
   POST /sync/orders
          │
          ▼
2. API Layer (routes/sync.py)
   - Parse request
   - Call use case
          │
          ▼
3. Application Layer (sync_orders.py)
   - Fetch from WooCommerce
   - Convert to domain model
   - Save to Odoo
          │
          ▼
4. Domain Layer (order.py)
   - Validate data
   - Apply business rules
   - Transform between formats
          │
          ▼
5. Infrastructure Layer
   - WooCommerceClient.get_orders()
   - OdooClient.create()
          │
          ▼
6. Response
   Return sync results
```

## Design Patterns

### 1. Repository Pattern
- Abstracts data access
- Located in `infrastructure/persistence/`
- Can store sync metadata, error logs, etc.

### 2. Use Case Pattern
- Each business operation is a use case
- Single responsibility
- Easy to test

### 3. Adapter Pattern
- `WooCommerceClient` and `OdooClient` are adapters
- Convert external API calls to domain operations

### 4. Factory Pattern
- `Order.from_woocommerce()`
- `Product.from_odoo()`
- Centralized object creation

## Dependency Direction

```
API → Application → Domain ← Infrastructure
```

**Key Rule**: Dependencies always point INWARD
- Domain has no dependencies
- Application depends on Domain
- Infrastructure depends on Domain (for interfaces)
- API depends on Application

## Testing Strategy

### Unit Tests
- Domain layer: Pure logic testing
- Application layer: Mock infrastructure
- Infrastructure layer: Mock external APIs

### Integration Tests
- Test API endpoints with test database
- Use test WooCommerce/Odoo instances

### Example Test Structure

```python
# Test domain model
def test_order_from_woocommerce():
    woo_data = {...}
    order = Order.from_woocommerce(woo_data)
    assert order.total == Decimal("100.00")

# Test use case (mock infrastructure)
async def test_sync_orders():
    mock_woo = MockWooClient()
    mock_odoo = MockOdooClient()
    use_case = SyncOrdersUseCase(mock_woo, mock_odoo)
    result = await use_case.execute()
    assert result["success"] == 5
```

## Extension Points

### Adding New Sync Types

1. Create domain model (if needed)
2. Create use case in `application/`
3. Add API route in `api/routes/`
4. Add tests

### Supporting New E-commerce Platform

1. Create new client in `infrastructure/`
2. Implement same interface as WooCommerceClient
3. Update use cases to support new client
4. Domain models remain unchanged

### Custom Field Mappings

Edit domain models:

```python
# domain/order.py
def to_odoo_values(self):
    return {
        "name": self.order_number,
        "x_custom_field": self.custom_data,  # Add here
    }
```

## Configuration Management

- **Settings**: Centralized in `config/settings.py`
- **Environment**: `.env` file for secrets
- **Type Safety**: Pydantic models for validation

## Error Handling

### Strategy

1. **Infrastructure Layer**: Catch and log HTTP errors
2. **Application Layer**: Handle business errors
3. **API Layer**: Convert to HTTP responses

### Example

```python
# Infrastructure
try:
    response = await self.client.get(url)
except httpx.HTTPError as e:
    logger.error(f"API error: {e}")
    raise

# Application
try:
    await use_case.execute()
except Exception as e:
    return {"success": False, "error": str(e)}

# API
try:
    result = await sync_orders()
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

## Logging

- **Library**: Loguru
- **Levels**: INFO for operations, ERROR for failures
- **Format**: Structured logging with context
- **Storage**: Files in `logs/` directory

## Security Considerations

1. **API Keys**: Stored in environment variables
2. **HTTPS**: Required for production
3. **Webhook Validation**: Optional signature verification
4. **Rate Limiting**: Can be added to API layer
5. **Input Validation**: Pydantic models at API boundaries

## Performance

### Optimization Strategies

1. **Async/Await**: Non-blocking I/O throughout
2. **Batch Processing**: Paginated fetching from APIs
3. **Connection Pooling**: Reuse HTTP connections
4. **Caching**: Can add Redis for frequently accessed data

### Scalability

- **Horizontal**: Run multiple API instances
- **Vertical**: Increase resources per instance
- **Database**: PostgreSQL with connection pooling
- **Queue**: Can add Celery for background jobs

## Future Enhancements

1. **Event Sourcing**: Track all sync events
2. **CQRS**: Separate read/write models
3. **Retry Logic**: Automatic retry with exponential backoff
4. **Circuit Breaker**: Fail fast when external service is down
5. **Metrics**: Prometheus/Grafana integration
6. **Multi-tenancy**: Support multiple WooCommerce/Odoo instances

## References

- Clean Architecture by Robert C. Martin
- FastAPI Documentation
- WooCommerce REST API Docs
- Odoo External API Documentation
