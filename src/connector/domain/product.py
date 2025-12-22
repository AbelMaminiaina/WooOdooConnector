from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal


@dataclass
class Product:
    """Domain model for a product (platform-agnostic)"""

    # Common fields
    external_id: str  # ID from source system
    name: str
    sku: Optional[str] = None
    description: Optional[str] = None

    # Pricing
    price: Decimal = Decimal("0")
    sale_price: Optional[Decimal] = None
    regular_price: Optional[Decimal] = None

    # Inventory
    stock_quantity: Optional[int] = None
    manage_stock: bool = False
    stock_status: str = "instock"  # instock, outofstock, onbackorder

    # Product info
    type: str = "simple"  # simple, variable, grouped, etc.
    status: str = "publish"  # publish, draft, private
    weight: Optional[str] = None

    # Categories and attributes
    categories: list = None

    # Sync metadata
    woo_id: Optional[int] = None
    odoo_id: Optional[int] = None
    synced_at: Optional[datetime] = None
    sync_status: str = "pending"

    def __post_init__(self):
        if self.categories is None:
            self.categories = []

    @classmethod
    def from_woocommerce(cls, woo_product: dict) -> "Product":
        """Create Product from WooCommerce product data

        Args:
            woo_product: WooCommerce product dictionary

        Returns:
            Product domain model
        """
        return cls(
            external_id=str(woo_product["id"]),
            woo_id=woo_product["id"],
            name=woo_product.get("name", ""),
            sku=woo_product.get("sku"),
            description=woo_product.get("description"),
            price=Decimal(str(woo_product.get("price", 0))),
            sale_price=(
                Decimal(str(woo_product["sale_price"]))
                if woo_product.get("sale_price")
                else None
            ),
            regular_price=Decimal(str(woo_product.get("regular_price", 0))),
            stock_quantity=woo_product.get("stock_quantity"),
            manage_stock=woo_product.get("manage_stock", False),
            stock_status=woo_product.get("stock_status", "instock"),
            type=woo_product.get("type", "simple"),
            status=woo_product.get("status", "publish"),
            weight=woo_product.get("weight"),
            categories=[cat.get("name") for cat in woo_product.get("categories", [])],
        )

    @classmethod
    def from_odoo(cls, odoo_product: dict) -> "Product":
        """Create Product from Odoo product data

        Args:
            odoo_product: Odoo product.product dictionary

        Returns:
            Product domain model
        """
        return cls(
            external_id=str(odoo_product["id"]),
            odoo_id=odoo_product["id"],
            name=odoo_product.get("name", ""),
            sku=odoo_product.get("default_code"),  # SKU in Odoo
            description=odoo_product.get("description_sale"),
            price=Decimal(str(odoo_product.get("list_price", 0))),
            stock_quantity=int(odoo_product.get("qty_available", 0)),
            manage_stock=True,
            stock_status=(
                "instock" if odoo_product.get("qty_available", 0) > 0 else "outofstock"
            ),
            type="simple",
            weight=(
                str(odoo_product.get("weight")) if odoo_product.get("weight") else None
            ),
        )

    def to_odoo_values(self) -> dict:
        """Convert to Odoo product.product values

        Returns:
            Dictionary of Odoo field values
        """
        values = {
            "name": self.name,
            "default_code": self.sku,
            "list_price": float(self.price),
            "description_sale": self.description,
            "type": "product",  # Odoo uses 'product' for stockable items
        }

        if self.weight:
            try:
                values["weight"] = float(self.weight)
            except (ValueError, TypeError):
                pass

        return values

    def to_woocommerce_values(self) -> dict:
        """Convert to WooCommerce product values

        Returns:
            Dictionary of WooCommerce field values
        """
        values = {
            "name": self.name,
            "sku": self.sku,
            "regular_price": str(self.regular_price or self.price),
            "description": self.description,
            "manage_stock": self.manage_stock,
            "stock_status": self.stock_status,
            "type": self.type,
            "status": self.status,
        }

        if self.stock_quantity is not None:
            values["stock_quantity"] = self.stock_quantity

        if self.sale_price:
            values["sale_price"] = str(self.sale_price)

        if self.weight:
            values["weight"] = self.weight

        return values
