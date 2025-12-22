# Quick Start Guide

Get your WooCommerce-Odoo connector running in 5 minutes!

## Step 1: Get API Credentials

### WooCommerce API Keys

1. Login to WordPress admin
2. Go to **WooCommerce > Settings > Advanced > REST API**
3. Click **Add key**
4. Fill in:
   - Description: "Odoo Connector"
   - User: Select admin user
   - Permissions: Read/Write
5. Click **Generate API key**
6. **IMPORTANT**: Copy the Consumer Key and Consumer Secret immediately!

### Odoo API Access

You need:
- Odoo URL (e.g., `https://yourcompany.odoo.com`)
- Database name
- Username (admin or API user)
- Password

Test your Odoo access at: `https://yourcompany.odoo.com/web/login`

## Step 2: Configure the Connector

```bash
# Clone the project
git clone <your-repo>
cd WooOdooConnector

# Copy environment template
cp .env.example .env
```

Edit `.env`:

```bash
# WooCommerce
WOO_URL=https://your-shop.com
WOO_CONSUMER_KEY=ck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WOO_CONSUMER_SECRET=cs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Odoo
ODOO_URL=https://yourcompany.odoo.com
ODOO_DB=your_database_name
ODOO_USERNAME=admin
ODOO_PASSWORD=your_password

# API (generate random key)
API_SECRET_KEY=your-secret-key-here-change-this
```

## Step 3: Run with Docker (Easiest)

```bash
# Start everything
docker-compose up -d

# Check if it's running
curl http://localhost:8000/health

# View logs
docker-compose logs -f
```

## Step 4: Run Locally (Development)

```bash
# Install Python 3.11+ if needed

# Install dependencies
pip install -r requirements.txt

# Run
python run.py
```

## Step 5: Test It!

Open your browser: http://localhost:8000/docs

### Test 1: Sync Recent Orders

```bash
curl -X POST "http://localhost:8000/sync/orders?since_days=7&limit=10"
```

### Test 2: Sync Stock

```bash
curl -X POST "http://localhost:8000/sync/stock"
```

## Step 6: Set Up Webhooks (Optional)

In WooCommerce:

1. Go to **WooCommerce > Settings > Advanced > Webhooks**
2. Click **Add webhook**
3. Configure:
   - Name: "Odoo Order Sync"
   - Status: Active
   - Topic: "Order created"
   - Delivery URL: `http://your-server:8000/webhooks/woocommerce/order`
4. Save

Now orders will sync automatically!

## Troubleshooting

### Can't connect to WooCommerce?

Test the API directly:
```bash
curl https://your-shop.com/wp-json/wc/v3/products \
  -u "your_consumer_key:your_consumer_secret"
```

### Can't connect to Odoo?

- Make sure you can login at `https://your-odoo.com/web/login`
- Check database name (usually company name)
- Verify username and password

### Port 8000 already in use?

Change in `.env`:
```bash
API_PORT=8080
```

## Next Steps

- Read the full [README.md](README.md)
- Customize field mappings in `src/connector/domain/`
- Set up scheduled syncs with cron
- Deploy to production

## Support

Need help? Create an issue or contact support.

---

Happy syncing!
