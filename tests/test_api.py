"""
Tests for API endpoints
"""

import pytest
from httpx import AsyncClient, ASGITransport

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from connector.api.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "WooCommerce <-> Odoo Connector"
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_sync_status_endpoint():
    """Test sync status endpoint"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/sync/status")

    assert response.status_code == 200
    data = response.json()
    assert "woo_url" in data
    assert "odoo_url" in data
    assert "sync_enabled" in data


@pytest.mark.asyncio
async def test_webhook_test_endpoint():
    """Test webhook test endpoint"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/webhooks/test")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
