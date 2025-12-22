from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from decimal import Decimal


@dataclass
class OrderLine:
    """Order line item"""

    product_id: int
    product_name: str
    quantity: float
    unit_price: Decimal
    total: Decimal
    sku: Optional[str] = None
    tax: Optional[Decimal] = None


@dataclass
class OrderAddress:
    """Shipping/Billing address"""

    first_name: str
    last_name: str
    company: Optional[str] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


@dataclass
class Order:
    """Domain model for an order (platform-agnostic)"""

    # Common fields
    external_id: str  # ID from source system (WooCommerce)
    order_number: str
    status: str
    date_created: datetime
    customer_email: str
    customer_name: str

    # Financial
    total: Decimal
    subtotal: Decimal
    tax_total: Decimal
    shipping_total: Decimal
    currency: str

    # Lines
    lines: List[OrderLine]

    # Addresses
    billing_address: OrderAddress
    shipping_address: Optional[OrderAddress] = None

    # Optional fields
    customer_note: Optional[str] = None
    payment_method: Optional[str] = None
    payment_method_title: Optional[str] = None

    # Sync metadata
    odoo_id: Optional[int] = None
    synced_at: Optional[datetime] = None
    sync_status: str = "pending"  # pending, synced, error

    @classmethod
    def from_woocommerce(cls, woo_order: dict) -> "Order":
        """Create Order from WooCommerce order data

        Args:
            woo_order: WooCommerce order dictionary

        Returns:
            Order domain model
        """
        # Parse billing address
        billing = woo_order.get("billing", {})
        billing_address = OrderAddress(
            first_name=billing.get("first_name", ""),
            last_name=billing.get("last_name", ""),
            company=billing.get("company"),
            address_1=billing.get("address_1"),
            address_2=billing.get("address_2"),
            city=billing.get("city"),
            state=billing.get("state"),
            postcode=billing.get("postcode"),
            country=billing.get("country"),
            email=billing.get("email"),
            phone=billing.get("phone"),
        )

        # Parse shipping address
        shipping = woo_order.get("shipping", {})
        shipping_address = None
        if shipping.get("first_name"):
            shipping_address = OrderAddress(
                first_name=shipping.get("first_name", ""),
                last_name=shipping.get("last_name", ""),
                company=shipping.get("company"),
                address_1=shipping.get("address_1"),
                address_2=shipping.get("address_2"),
                city=shipping.get("city"),
                state=shipping.get("state"),
                postcode=shipping.get("postcode"),
                country=shipping.get("country"),
            )

        # Parse order lines
        lines = []
        for item in woo_order.get("line_items", []):
            line = OrderLine(
                product_id=item.get("product_id"),
                product_name=item.get("name"),
                quantity=float(item.get("quantity", 0)),
                unit_price=Decimal(str(item.get("price", 0))),
                total=Decimal(str(item.get("total", 0))),
                sku=item.get("sku"),
                tax=Decimal(str(item.get("total_tax", 0))),
            )
            lines.append(line)

        # Create order
        return cls(
            external_id=str(woo_order["id"]),
            order_number=woo_order.get("number", str(woo_order["id"])),
            status=woo_order.get("status", "pending"),
            date_created=datetime.fromisoformat(
                woo_order["date_created"].replace("Z", "+00:00")
            ),
            customer_email=billing.get("email", ""),
            customer_name=f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip(),
            total=Decimal(str(woo_order.get("total", 0))),
            subtotal=Decimal(str(woo_order.get("subtotal", 0))),
            tax_total=Decimal(str(woo_order.get("total_tax", 0))),
            shipping_total=Decimal(str(woo_order.get("shipping_total", 0))),
            currency=woo_order.get("currency", "USD"),
            lines=lines,
            billing_address=billing_address,
            shipping_address=shipping_address,
            customer_note=woo_order.get("customer_note"),
            payment_method=woo_order.get("payment_method"),
            payment_method_title=woo_order.get("payment_method_title"),
        )

    def to_odoo_values(self) -> dict:
        """Convert to Odoo sale.order values

        Returns:
            Dictionary of Odoo field values
        """
        # This would need to be customized based on your Odoo setup
        # Example basic mapping:
        values = {
            "name": self.order_number,
            "date_order": self.date_created.isoformat(),
            "amount_total": float(self.total),
            "state": self._map_status_to_odoo(),
            # You would need to create/find partner_id, order_line, etc.
            # This is just a basic example
        }

        return values

    def _map_status_to_odoo(self) -> str:
        """Map WooCommerce status to Odoo state"""
        mapping = {
            "pending": "draft",
            "processing": "sale",
            "completed": "done",
            "cancelled": "cancel",
            "refunded": "cancel",
        }
        return mapping.get(self.status, "draft")
