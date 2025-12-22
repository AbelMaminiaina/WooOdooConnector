# WooCommerce <-> Odoo Connector

A robust, production-ready connector to synchronize data between WooCommerce and Odoo.

## Features

- **Order Synchronization**: WooCommerce orders -> Odoo sales orders
- **Product Synchronization**: Bidirectional product sync
- **Stock Synchronization**: Odoo inventory -> WooCommerce stock
- **Webhook Support**: Real-time updates via WooCommerce webhooks
- **REST API**: Manual sync triggers and monitoring
- **Docker Support**: Easy deployment with Docker Compose
- **Clean Architecture**: Maintainable, testable code structure

## Legal & License Compliance

This connector is a **standalone external service** that communicates with WooCommerce and Odoo through their public APIs:

- Uses WooCommerce REST API (permissive license)
- Uses Odoo JSON-RPC API (public interface)
- **No AGPL code copied** - only API calls
- Can be sold as SaaS, licensed software, or installed on-premise

## Architecture

```
WooOdooConnector/
├── src/connector/
│   ├── api/              # FastAPI REST API
│   ├── application/      # Use cases (business logic)
│   ├── domain/           # Domain models
│   ├── infrastructure/   # External services (WooCommerce, Odoo)
│   └── config/           # Configuration
├── docker/               # Docker configuration
├── logs/                 # Application logs
└── docker-compose.yml    # Docker Compose setup
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- WooCommerce store with API credentials
- Odoo instance with API access

### 1. Clone & Configure

```bash
git clone <your-repo>
cd WooOdooConnector

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 2. Configuration

Edit `.env` file:

```bash
# WooCommerce
WOO_URL=https://your-shop.com
WOO_CONSUMER_KEY=ck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WOO_CONSUMER_SECRET=cs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Odoo
ODOO_URL=https://your-odoo.com
ODOO_DB=your_database
ODOO_USERNAME=admin
ODOO_PASSWORD=your_password

# API
API_SECRET_KEY=generate-a-random-secret-key
```

### 3. Run with Docker (Recommended)

```bash
# Build and start
docker-compose up -d

# Check logs
docker-compose logs -f connector

# Access API documentation
# Open http://localhost:8000/docs
```

### 4. Run Locally (Development)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Run the API
python -m uvicorn connector.api.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

Access the interactive API documentation at `http://localhost:8000/docs`

### Sync Endpoints

#### Sync Orders (WooCommerce -> Odoo)
```bash
POST /sync/orders
# Optional query parameters:
# - status: Order status filter (processing, completed)
# - since_days: Only sync orders from last N days
# - limit: Maximum number of orders

curl -X POST "http://localhost:8000/sync/orders?status=processing&since_days=7"
```

#### Sync Products (WooCommerce -> Odoo)
```bash
POST /sync/products/woo-to-odoo

curl -X POST "http://localhost:8000/sync/products/woo-to-odoo?limit=100"
```

#### Sync Products (Odoo -> WooCommerce)
```bash
POST /sync/products/odoo-to-woo

curl -X POST "http://localhost:8000/sync/products/odoo-to-woo"
```

#### Sync Stock (Odoo -> WooCommerce)
```bash
POST /sync/stock
# Optional query parameters:
# - sku: Specific product SKU to sync

# Sync all products
curl -X POST "http://localhost:8000/sync/stock"

# Sync specific product
curl -X POST "http://localhost:8000/sync/stock?sku=PRODUCT-123"
```

### Webhook Endpoints

Configure these URLs in WooCommerce (Settings > Advanced > Webhooks):

```bash
# Order webhooks
POST /webhooks/woocommerce/order
Topics: order.created, order.updated, order.deleted

# Product webhooks
POST /webhooks/woocommerce/product
Topics: product.created, product.updated, product.deleted

# Stock webhooks (from Odoo)
POST /webhooks/odoo/stock
```

### Monitoring Endpoints

```bash
# Health check
GET /health

# Sync status
GET /sync/status
```

## WooCommerce Webhook Configuration

1. Go to WooCommerce > Settings > Advanced > Webhooks
2. Click "Add webhook"
3. Configure:
   - **Name**: Odoo Order Sync
   - **Status**: Active
   - **Topic**: Order created / Order updated
   - **Delivery URL**: `https://your-connector.com/webhooks/woocommerce/order`
   - **Secret**: (optional, for validation)
   - **API Version**: WP REST API Integration v3

## Odoo Configuration

### Custom Fields

Add these fields to Odoo models (optional but recommended):

```python
# sale.order - WooCommerce Order ID
x_woocommerce_id = fields.Char(string="WooCommerce ID")

# product.product - WooCommerce Product ID
x_woocommerce_id = fields.Char(string="WooCommerce ID")
```

### Automation (Stock Sync)

Create an Odoo automation to trigger stock updates:

1. Go to Settings > Technical > Automation
2. Create automation on `product.product`
3. Trigger: On Update
4. Domain: `[('qty_available', '!=', False)]`
5. Action: Execute Python Code
   ```python
   import requests

   url = "https://your-connector.com/webhooks/odoo/stock"
   data = {
       "sku": record.default_code,
       "quantity": int(record.qty_available)
   }
   requests.post(url, json=data)
   ```

## Scheduled Synchronization

You can set up scheduled syncs using cron or task schedulers:

```bash
# Example cron job (sync orders every 15 minutes)
*/15 * * * * curl -X POST http://localhost:8000/sync/orders?since_days=1

# Sync stock every hour
0 * * * * curl -X POST http://localhost:8000/sync/stock
```

Or use APScheduler (extend the application):

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(sync_orders, 'interval', minutes=15)
scheduler.start()
```

## Deployment

### Production Checklist

- [ ] Update `.env` with production credentials
- [ ] Set strong `API_SECRET_KEY`
- [ ] Configure CORS in `api/main.py` (restrict origins)
- [ ] Set up HTTPS/SSL certificate
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerting
- [ ] Configure log rotation
- [ ] Set up database backups
- [ ] Review and adjust sync intervals

### Docker Production

```bash
# Build for production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale if needed
docker-compose up -d --scale connector=3
```

### Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name connector.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Customization

### Mapping Custom Fields

Edit the domain models to add custom field mappings:

**src/connector/domain/order.py**
```python
def to_odoo_values(self) -> dict:
    values = {
        "name": self.order_number,
        "date_order": self.date_created.isoformat(),
        "amount_total": float(self.total),
        # Add your custom fields here
        "x_custom_field": self.some_value,
    }
    return values
```

### Adding New Sync Types

1. Create new use case in `application/`
2. Add route in `api/routes/sync.py`
3. Implement business logic

## Troubleshooting

### Connection Issues

```bash
# Test WooCommerce connection
curl https://shop.com/wp-json/wc/v3/products \
  -u "consumer_key:consumer_secret"

# Test Odoo connection
curl -X POST https://odoo.com/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"service":"common","method":"version"},"id":1}'
```

### View Logs

```bash
# Docker logs
docker-compose logs -f connector

# Local logs
tail -f logs/connector.log
```

### Debug Mode

Set in `.env`:
```bash
LOG_LEVEL=DEBUG
```

## Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx-mock

# Run tests
pytest

# With coverage
pytest --cov=connector --cov-report=html
```

## Business Models

This connector can be monetized as:

- **SaaS**: Host and charge monthly subscription
- **Licensed Software**: Sell annual licenses
- **Custom Integration**: Charge for installation and customization
- **Managed Service**: Offer as part of consulting services

## Support

For issues, questions, or contributions:

- GitHub Issues: <your-repo>/issues
- Documentation: <your-docs-url>
- Email: support@yourdomain.com

## License

This software is proprietary. Contact for licensing information.

## Credits

Built with:
- FastAPI
- Pydantic
- HTTPX
- Loguru
- PostgreSQL
- Docker

---

Made with care for seamless WooCommerce-Odoo integration.
