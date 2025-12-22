# Deployment Guide

Complete guide for deploying the WooCommerce-Odoo Connector to production.

## Prerequisites

- Server with Ubuntu 20.04+ (or similar Linux distribution)
- Docker and Docker Compose installed
- Domain name pointed to your server
- SSL certificate (Let's Encrypt recommended)

## Option 1: Docker Deployment (Recommended)

### 1. Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

### 2. Deploy Application

```bash
# Create application directory
mkdir -p /opt/woo-odoo-connector
cd /opt/woo-odoo-connector

# Clone repository
git clone <your-repo> .

# Create .env file
cp .env.example .env
nano .env  # Edit with production credentials

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f
```

### 3. Configure Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt install nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/connector
```

Add this configuration:

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

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/connector /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### 4. Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d connector.yourdomain.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

## Option 2: Systemd Service (No Docker)

### 1. Prepare Environment

```bash
# Create user
sudo useradd -r -s /bin/false connector

# Create directory
sudo mkdir -p /opt/woo-odoo-connector
sudo chown connector:connector /opt/woo-odoo-connector

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip

# Clone repository
cd /opt/woo-odoo-connector
sudo -u connector git clone <your-repo> .

# Create virtual environment
sudo -u connector python3.11 -m venv venv

# Install dependencies
sudo -u connector ./venv/bin/pip install -r requirements.txt
```

### 2. Create Systemd Service

```bash
sudo nano /etc/systemd/system/connector.service
```

Add:

```ini
[Unit]
Description=WooCommerce Odoo Connector
After=network.target

[Service]
Type=simple
User=connector
Group=connector
WorkingDirectory=/opt/woo-odoo-connector
Environment="PYTHONPATH=/opt/woo-odoo-connector/src"
EnvironmentFile=/opt/woo-odoo-connector/.env
ExecStart=/opt/woo-odoo-connector/venv/bin/python -m uvicorn connector.api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start connector

# Enable on boot
sudo systemctl enable connector

# Check status
sudo systemctl status connector
```

## Option 3: Cloud Platforms

### AWS ECS

1. Build Docker image
2. Push to ECR
3. Create ECS task definition
4. Deploy to ECS Fargate

### Google Cloud Run

```bash
# Build and deploy
gcloud run deploy connector \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name connector \
  --image myregistry.azurecr.io/connector:latest \
  --dns-name-label connector \
  --ports 8000
```

### Heroku

```bash
# Login
heroku login

# Create app
heroku create woo-odoo-connector

# Set environment variables
heroku config:set WOO_URL=https://shop.com
heroku config:set ODOO_URL=https://odoo.com
# ... etc

# Deploy
git push heroku main
```

## Database Setup

### PostgreSQL on Server

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE woo_odoo_connector;
CREATE USER connector WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE woo_odoo_connector TO connector;
\q

# Update .env
DATABASE_URL=postgresql://connector:strong_password@localhost:5432/woo_odoo_connector
```

### Managed Database (Recommended for Production)

- **AWS RDS**: PostgreSQL instance
- **Google Cloud SQL**: Managed PostgreSQL
- **Azure Database**: For PostgreSQL
- **DigitalOcean Managed Database**

Update `DATABASE_URL` in `.env` with connection string.

## Monitoring & Logging

### 1. Application Logs

```bash
# Docker logs
docker-compose logs -f connector

# Systemd logs
sudo journalctl -u connector -f

# Log files
tail -f /opt/woo-odoo-connector/logs/connector.log
```

### 2. Setup Log Rotation

```bash
sudo nano /etc/logrotate.d/connector
```

```
/opt/woo-odoo-connector/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 connector connector
    sharedscripts
    postrotate
        systemctl reload connector
    endscript
}
```

### 3. Monitoring with Prometheus (Optional)

Install Prometheus exporter and configure metrics collection.

## Backup Strategy

### Database Backups

```bash
# Create backup script
sudo nano /opt/backup-db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T db pg_dump -U connector woo_odoo_connector | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
```

```bash
# Make executable
sudo chmod +x /opt/backup-db.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
0 2 * * * /opt/backup-db.sh
```

## Security Hardening

### 1. Firewall

```bash
# Install ufw
sudo apt install ufw

# Allow SSH, HTTP, HTTPS
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# Enable firewall
sudo ufw enable
```

### 2. Fail2Ban

```bash
# Install
sudo apt install fail2ban

# Configure
sudo nano /etc/fail2ban/jail.local
```

### 3. Environment Variables

Never commit `.env` to git. Use secrets management:

- **AWS Secrets Manager**
- **Google Cloud Secret Manager**
- **Azure Key Vault**
- **HashiCorp Vault**

### 4. Rate Limiting

Add rate limiting to Nginx:

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location / {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://localhost:8000;
}
```

## Performance Tuning

### 1. Worker Processes

Update `docker-compose.yml`:

```yaml
command: uvicorn connector.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Database Connection Pooling

Update `settings.py`:

```python
DATABASE_URL = "postgresql://user:pass@host:5432/db?pool_size=20&max_overflow=0"
```

### 3. Caching (Optional)

Add Redis for caching:

```yaml
# docker-compose.yml
redis:
  image: redis:alpine
  ports:
    - "6379:6379"
```

## Scheduled Syncs

### Cron Jobs

```bash
# Edit crontab
crontab -e

# Sync orders every 15 minutes
*/15 * * * * curl -X POST http://localhost:8000/sync/orders?since_days=1

# Sync stock every hour
0 * * * * curl -X POST http://localhost:8000/sync/stock

# Sync products daily at 3 AM
0 3 * * * curl -X POST http://localhost:8000/sync/products/odoo-to-woo
```

### Systemd Timers (Alternative)

More robust than cron for system services.

## Health Checks

### 1. Uptime Monitoring

Use services like:
- UptimeRobot
- Pingdom
- StatusCake

Monitor: `https://connector.yourdomain.com/health`

### 2. Application Monitoring

- Sentry for error tracking
- New Relic for APM
- Datadog for infrastructure

## Scaling

### Horizontal Scaling

```bash
# Scale with Docker Compose
docker-compose up -d --scale connector=3

# Use load balancer (Nginx, HAProxy)
```

### Vertical Scaling

Increase server resources (CPU, RAM).

## Troubleshooting

### Container Won't Start

```bash
docker-compose logs connector
docker-compose down && docker-compose up -d
```

### Connection Refused

- Check firewall rules
- Verify Nginx configuration
- Check service status

### High Memory Usage

- Reduce worker processes
- Enable connection pooling
- Add memory limits to Docker

## Maintenance

### Updates

```bash
# Pull latest code
git pull

# Rebuild containers
docker-compose up -d --build

# Or restart service
sudo systemctl restart connector
```

### Database Migration

Use Alembic for schema changes:

```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Rollback Plan

```bash
# Tag before deployment
git tag v1.0.0
git push --tags

# Rollback if needed
git checkout v1.0.0
docker-compose up -d --build
```

## Support

For production issues:
- Check logs first
- Review monitoring dashboards
- Contact support team

---

**Production Checklist**:
- [ ] SSL certificate configured
- [ ] Environment variables secured
- [ ] Database backups automated
- [ ] Monitoring in place
- [ ] Firewall configured
- [ ] Logs rotating
- [ ] Health checks enabled
- [ ] Documentation updated
