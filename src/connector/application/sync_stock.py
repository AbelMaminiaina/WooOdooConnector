from typing import Optional
from loguru import logger

from ..infrastructure.woocommerce import WooCommerceClient
from ..infrastructure.odoo import OdooClient


class SyncStockUseCase:
    """Use case for synchronizing stock levels from Odoo to WooCommerce"""

    def __init__(self, woo_client: WooCommerceClient, odoo_client: OdooClient):
        """Initialize use case

        Args:
            woo_client: WooCommerce API client
            odoo_client: Odoo API client
        """
        self.woo_client = woo_client
        self.odoo_client = odoo_client

    async def execute(self, sku: Optional[str] = None) -> dict:
        """Sync stock levels from Odoo to WooCommerce

        Args:
            sku: Optional SKU to sync specific product, otherwise sync all

        Returns:
            Dictionary with sync results
        """
        logger.info("Starting stock synchronization from Odoo to WooCommerce")

        results = {"total": 0, "success": 0, "failed": 0, "errors": []}

        try:
            if sku:
                # Sync single product by SKU
                await self._sync_product_stock(sku, results)
            else:
                # Sync all products
                await self._sync_all_stock(results)

            logger.info(
                f"Stock sync completed: {results['success']} success, "
                f"{results['failed']} failed out of {results['total']} total"
            )

            return results

        except Exception as e:
            logger.error(f"Stock sync failed: {e}")
            raise

    async def _sync_all_stock(self, results: dict):
        """Sync stock for all products

        Args:
            results: Results dictionary to update
        """
        # Get all products from Odoo with stock info
        products = await self.odoo_client.search_read(
            "product.product",
            domain=[["sale_ok", "=", True], ["default_code", "!=", False]],  # Has SKU
            fields=["default_code", "qty_available"],
        )

        results["total"] = len(products)
        logger.info(f"Found {len(products)} products in Odoo")

        for product in products:
            sku = product.get("default_code")
            stock_qty = int(product.get("qty_available", 0))

            try:
                await self._update_woo_stock(sku, stock_qty)
                results["success"] += 1

            except Exception as e:
                results["failed"] += 1
                error_msg = f"Failed to update stock for {sku}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)

    async def _sync_product_stock(self, sku: str, results: dict):
        """Sync stock for a specific product

        Args:
            sku: Product SKU
            results: Results dictionary to update
        """
        results["total"] = 1

        # Get product from Odoo
        products = await self.odoo_client.search_read(
            "product.product",
            domain=[["default_code", "=", sku]],
            fields=["qty_available"],
            limit=1,
        )

        if not products:
            results["failed"] = 1
            error_msg = f"Product {sku} not found in Odoo"
            results["errors"].append(error_msg)
            logger.error(error_msg)
            return

        stock_qty = int(products[0].get("qty_available", 0))

        try:
            await self._update_woo_stock(sku, stock_qty)
            results["success"] = 1
            logger.info(f"Updated stock for {sku}: {stock_qty}")

        except Exception as e:
            results["failed"] = 1
            error_msg = f"Failed to update stock for {sku}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)

    async def _update_woo_stock(self, sku: str, quantity: int):
        """Update stock in WooCommerce for a product

        Args:
            sku: Product SKU
            quantity: Stock quantity
        """
        # Find product in WooCommerce by SKU
        woo_products = await self.woo_client.get_products(sku=sku)

        if not woo_products:
            raise Exception(f"Product {sku} not found in WooCommerce")

        woo_product = woo_products[0]
        product_id = woo_product["id"]

        # Update stock
        await self.woo_client.update_product_stock(product_id, quantity)

        logger.info(
            f"Updated WooCommerce product {product_id} ({sku}) stock to {quantity}"
        )
