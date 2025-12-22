from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger

from ..infrastructure.woocommerce import WooCommerceClient
from ..infrastructure.odoo import OdooClient
from ..domain.order import Order


class SyncOrdersUseCase:
    """Use case for synchronizing orders from WooCommerce to Odoo"""

    def __init__(self, woo_client: WooCommerceClient, odoo_client: OdooClient):
        """Initialize use case

        Args:
            woo_client: WooCommerce API client
            odoo_client: Odoo API client
        """
        self.woo_client = woo_client
        self.odoo_client = odoo_client

    async def execute(
        self,
        status: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> dict:
        """Sync orders from WooCommerce to Odoo

        Args:
            status: Filter by order status (e.g., 'processing')
            since: Only sync orders after this date
            limit: Maximum number of orders to sync

        Returns:
            Dictionary with sync results
        """
        logger.info("Starting order synchronization from WooCommerce to Odoo")

        results = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "errors": []
        }

        try:
            # Get orders from WooCommerce
            woo_orders = await self._fetch_woocommerce_orders(status, since, limit)
            results["total"] = len(woo_orders)

            logger.info(f"Found {len(woo_orders)} orders to sync")

            # Process each order
            for woo_order in woo_orders:
                try:
                    await self._sync_single_order(woo_order)
                    results["success"] += 1
                    logger.info(f"Successfully synced order {woo_order['id']}")

                except Exception as e:
                    results["failed"] += 1
                    error_msg = f"Failed to sync order {woo_order['id']}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            logger.info(
                f"Order sync completed: {results['success']} success, "
                f"{results['failed']} failed out of {results['total']} total"
            )

            return results

        except Exception as e:
            logger.error(f"Order sync failed: {e}")
            raise

    async def _fetch_woocommerce_orders(
        self,
        status: Optional[str],
        since: Optional[datetime],
        limit: Optional[int]
    ) -> List[dict]:
        """Fetch orders from WooCommerce

        Args:
            status: Order status filter
            since: Date filter
            limit: Maximum number of orders

        Returns:
            List of WooCommerce order dictionaries
        """
        orders = []
        page = 1
        per_page = 100

        after = since.isoformat() if since else None

        while True:
            batch = await self.woo_client.get_orders(
                status=status,
                per_page=per_page,
                page=page,
                after=after
            )

            if not batch:
                break

            orders.extend(batch)

            # Check if we've reached the limit
            if limit and len(orders) >= limit:
                orders = orders[:limit]
                break

            # Check if there are more pages
            if len(batch) < per_page:
                break

            page += 1

        return orders

    async def _sync_single_order(self, woo_order: dict):
        """Sync a single order to Odoo

        Args:
            woo_order: WooCommerce order dictionary
        """
        # Convert WooCommerce order to domain model
        order = Order.from_woocommerce(woo_order)

        # Check if order already exists in Odoo
        existing = await self._find_existing_order(order.external_id)

        if existing:
            logger.info(f"Order {order.external_id} already exists in Odoo (ID: {existing})")
            # Optionally update the order
            # await self._update_order_in_odoo(existing, order)
            return existing

        # Create customer/partner if needed
        partner_id = await self._get_or_create_partner(order)

        # Create order in Odoo
        odoo_order_id = await self._create_order_in_odoo(order, partner_id)

        logger.info(
            f"Created order {order.external_id} in Odoo with ID {odoo_order_id}"
        )

        return odoo_order_id

    async def _find_existing_order(self, external_id: str) -> Optional[int]:
        """Find existing order in Odoo by external ID

        Args:
            external_id: WooCommerce order ID

        Returns:
            Odoo order ID if found, None otherwise
        """
        # Search for order with matching external reference
        # You might use a custom field like 'x_woocommerce_id' to store the external ID
        orders = await self.odoo_client.search(
            "sale.order",
            domain=[["x_woocommerce_id", "=", external_id]],
            limit=1
        )

        return orders[0] if orders else None

    async def _get_or_create_partner(self, order: Order) -> int:
        """Get or create customer/partner in Odoo

        Args:
            order: Order domain model

        Returns:
            Odoo partner (customer) ID
        """
        # Search for existing partner by email
        partners = await self.odoo_client.search(
            "res.partner",
            domain=[["email", "=", order.customer_email]],
            limit=1
        )

        if partners:
            return partners[0]

        # Create new partner
        partner_values = {
            "name": order.customer_name or order.customer_email,
            "email": order.customer_email,
            "phone": order.billing_address.phone,
            "street": order.billing_address.address_1,
            "street2": order.billing_address.address_2,
            "city": order.billing_address.city,
            "zip": order.billing_address.postcode,
            "country_id": await self._get_country_id(order.billing_address.country),
            "customer_rank": 1,
        }

        partner_id = await self.odoo_client.create("res.partner", partner_values)
        logger.info(f"Created partner {partner_id} for {order.customer_email}")

        return partner_id

    async def _get_country_id(self, country_code: Optional[str]) -> Optional[int]:
        """Get Odoo country ID from country code

        Args:
            country_code: ISO country code (e.g., 'US', 'FR')

        Returns:
            Odoo country ID or None
        """
        if not country_code:
            return None

        countries = await self.odoo_client.search(
            "res.country",
            domain=[["code", "=", country_code]],
            limit=1
        )

        return countries[0] if countries else None

    async def _create_order_in_odoo(self, order: Order, partner_id: int) -> int:
        """Create sale order in Odoo

        Args:
            order: Order domain model
            partner_id: Odoo partner ID

        Returns:
            Created order ID
        """
        # Prepare order lines
        order_lines = []
        for line in order.lines:
            # Find product by SKU
            product_id = await self._find_product_by_sku(line.sku) if line.sku else None

            if product_id:
                order_line = (0, 0, {
                    "product_id": product_id,
                    "product_uom_qty": line.quantity,
                    "price_unit": float(line.unit_price),
                })
                order_lines.append(order_line)
            else:
                logger.warning(f"Product not found for SKU {line.sku}, skipping line")

        # Create order
        order_values = {
            "partner_id": partner_id,
            "date_order": order.date_created.isoformat(),
            "x_woocommerce_id": order.external_id,  # Custom field to store WooCommerce ID
            "order_line": order_lines,
            "note": order.customer_note,
        }

        order_id = await self.odoo_client.create("sale.order", order_values)

        return order_id

    async def _find_product_by_sku(self, sku: str) -> Optional[int]:
        """Find product in Odoo by SKU

        Args:
            sku: Product SKU

        Returns:
            Odoo product ID or None
        """
        products = await self.odoo_client.search(
            "product.product",
            domain=[["default_code", "=", sku]],
            limit=1
        )

        return products[0] if products else None
