"""
Tests for domain models
"""

import pytest
from decimal import Decimal
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from connector.domain.order import Order, OrderLine, OrderAddress
from connector.domain.product import Product


class TestOrder:
    """Test Order domain model"""

    def test_create_order_from_woocommerce(self):
        """Test creating Order from WooCommerce data"""
        woo_order = {
            "id": 123,
            "number": "ORD-123",
            "status": "processing",
            "date_created": "2025-01-01T10:00:00Z",
            "total": "100.00",
            "subtotal": "90.00",
            "total_tax": "10.00",
            "shipping_total": "0.00",
            "currency": "USD",
            "billing": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "1234567890",
                "address_1": "123 Main St",
                "city": "New York",
                "state": "NY",
                "postcode": "10001",
                "country": "US"
            },
            "line_items": [
                {
                    "product_id": 1,
                    "name": "Test Product",
                    "quantity": 2,
                    "price": "45.00",
                    "total": "90.00",
                    "sku": "TEST-001",
                    "total_tax": "10.00"
                }
            ]
        }

        order = Order.from_woocommerce(woo_order)

        assert order.external_id == "123"
        assert order.order_number == "ORD-123"
        assert order.status == "processing"
        assert order.customer_email == "john@example.com"
        assert order.total == Decimal("100.00")
        assert len(order.lines) == 1
        assert order.lines[0].sku == "TEST-001"
        assert order.billing_address.first_name == "John"

    def test_order_to_odoo_values(self):
        """Test converting Order to Odoo values"""
        order = Order(
            external_id="123",
            order_number="ORD-123",
            status="processing",
            date_created=datetime(2025, 1, 1, 10, 0, 0),
            customer_email="john@example.com",
            customer_name="John Doe",
            total=Decimal("100.00"),
            subtotal=Decimal("90.00"),
            tax_total=Decimal("10.00"),
            shipping_total=Decimal("0.00"),
            currency="USD",
            lines=[],
            billing_address=OrderAddress(
                first_name="John",
                last_name="Doe",
                email="john@example.com"
            )
        )

        odoo_values = order.to_odoo_values()

        assert odoo_values["name"] == "ORD-123"
        assert odoo_values["amount_total"] == 100.0
        assert odoo_values["state"] == "sale"


class TestProduct:
    """Test Product domain model"""

    def test_create_product_from_woocommerce(self):
        """Test creating Product from WooCommerce data"""
        woo_product = {
            "id": 456,
            "name": "Test Product",
            "sku": "TEST-001",
            "description": "A test product",
            "price": "45.00",
            "regular_price": "50.00",
            "sale_price": "45.00",
            "stock_quantity": 10,
            "manage_stock": True,
            "stock_status": "instock",
            "type": "simple",
            "status": "publish",
            "weight": "1.5",
            "categories": [
                {"name": "Electronics"}
            ]
        }

        product = Product.from_woocommerce(woo_product)

        assert product.external_id == "456"
        assert product.name == "Test Product"
        assert product.sku == "TEST-001"
        assert product.price == Decimal("45.00")
        assert product.stock_quantity == 10
        assert product.manage_stock is True
        assert "Electronics" in product.categories

    def test_create_product_from_odoo(self):
        """Test creating Product from Odoo data"""
        odoo_product = {
            "id": 789,
            "name": "Odoo Product",
            "default_code": "ODOO-001",
            "description_sale": "An Odoo product",
            "list_price": 99.99,
            "qty_available": 25,
            "weight": 2.0
        }

        product = Product.from_odoo(odoo_product)

        assert product.external_id == "789"
        assert product.name == "Odoo Product"
        assert product.sku == "ODOO-001"
        assert product.price == Decimal("99.99")
        assert product.stock_quantity == 25
        assert product.stock_status == "instock"

    def test_product_to_woocommerce_values(self):
        """Test converting Product to WooCommerce values"""
        product = Product(
            external_id="123",
            name="Test Product",
            sku="TEST-001",
            price=Decimal("45.00"),
            regular_price=Decimal("50.00"),
            sale_price=Decimal("45.00"),
            stock_quantity=10,
            manage_stock=True,
            stock_status="instock"
        )

        woo_values = product.to_woocommerce_values()

        assert woo_values["name"] == "Test Product"
        assert woo_values["sku"] == "TEST-001"
        assert woo_values["regular_price"] == "50.00"
        assert woo_values["sale_price"] == "45.00"
        assert woo_values["stock_quantity"] == 10
        assert woo_values["manage_stock"] is True

    def test_product_to_odoo_values(self):
        """Test converting Product to Odoo values"""
        product = Product(
            external_id="123",
            name="Test Product",
            sku="TEST-001",
            price=Decimal("45.00"),
            description="A test product",
            weight="1.5"
        )

        odoo_values = product.to_odoo_values()

        assert odoo_values["name"] == "Test Product"
        assert odoo_values["default_code"] == "TEST-001"
        assert odoo_values["list_price"] == 45.0
        assert odoo_values["weight"] == 1.5
