from typing import List, Optional
from loguru import logger

from ..infrastructure.woocommerce import WooCommerceClient
from ..infrastructure.odoo import OdooClient
from ..domain.product import Product


class SyncProductsUseCase:
    """Use case for synchronizing products between WooCommerce and Odoo"""

    def __init__(self, woo_client: WooCommerceClient, odoo_client: OdooClient):
        """Initialize use case

        Args:
            woo_client: WooCommerce API client
            odoo_client: Odoo API client
        """
        self.woo_client = woo_client
        self.odoo_client = odoo_client

    async def sync_from_odoo_to_woo(self, limit: Optional[int] = None) -> dict:
        """Sync products from Odoo to WooCommerce

        Args:
            limit: Maximum number of products to sync

        Returns:
            Dictionary with sync results
        """
        logger.info("Starting product sync from Odoo to WooCommerce")

        results = {"total": 0, "created": 0, "updated": 0, "failed": 0, "errors": []}

        try:
            # Get products from Odoo
            odoo_products = await self._fetch_odoo_products(limit)
            results["total"] = len(odoo_products)

            logger.info(f"Found {len(odoo_products)} products in Odoo")

            for odoo_product in odoo_products:
                try:
                    product = Product.from_odoo(odoo_product)
                    sku = product.sku

                    if not sku:
                        logger.warning(f"Skipping product {product.name} - no SKU")
                        continue

                    # Check if product exists in WooCommerce
                    woo_products = await self.woo_client.get_products(sku=sku)

                    if woo_products:
                        # Update existing product
                        woo_id = woo_products[0]["id"]
                        await self.woo_client.update_product(
                            woo_id, product.to_woocommerce_values()
                        )
                        results["updated"] += 1
                        logger.info(f"Updated product {sku} in WooCommerce")
                    else:
                        # Product doesn't exist in WooCommerce
                        # Note: Creating products requires more data
                        logger.warning(f"Product {sku} not found in WooCommerce")

                except Exception as e:
                    results["failed"] += 1
                    error_msg = f"Failed to sync product: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            logger.info(
                f"Product sync completed: {results['updated']} updated, "
                f"{results['failed']} failed"
            )

            return results

        except Exception as e:
            logger.error(f"Product sync failed: {e}")
            raise

    async def sync_from_woo_to_odoo(self, limit: Optional[int] = None) -> dict:
        """Sync products from WooCommerce to Odoo

        Args:
            limit: Maximum number of products to sync

        Returns:
            Dictionary with sync results
        """
        logger.info("Starting product sync from WooCommerce to Odoo")

        results = {"total": 0, "created": 0, "updated": 0, "failed": 0, "errors": []}

        try:
            # Get products from WooCommerce
            woo_products = await self._fetch_woocommerce_products(limit)
            results["total"] = len(woo_products)

            logger.info(f"Found {len(woo_products)} products in WooCommerce")

            for woo_product in woo_products:
                try:
                    product = Product.from_woocommerce(woo_product)
                    sku = product.sku

                    if not sku:
                        logger.warning(f"Skipping product {product.name} - no SKU")
                        continue

                    # Check if product exists in Odoo
                    odoo_products = await self.odoo_client.search(
                        "product.product", domain=[["default_code", "=", sku]], limit=1
                    )

                    if odoo_products:
                        # Update existing product
                        await self.odoo_client.write(
                            "product.product", odoo_products, product.to_odoo_values()
                        )
                        results["updated"] += 1
                        logger.info(f"Updated product {sku} in Odoo")
                    else:
                        # Create new product
                        odoo_id = await self.odoo_client.create(
                            "product.product", product.to_odoo_values()
                        )
                        results["created"] += 1
                        logger.info(f"Created product {sku} in Odoo (ID: {odoo_id})")

                except Exception as e:
                    results["failed"] += 1
                    error_msg = f"Failed to sync product {woo_product.get('sku', 'unknown')}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            logger.info(
                f"Product sync completed: {results['created']} created, "
                f"{results['updated']} updated, {results['failed']} failed"
            )

            return results

        except Exception as e:
            logger.error(f"Product sync failed: {e}")
            raise

    async def _fetch_woocommerce_products(self, limit: Optional[int]) -> List[dict]:
        """Fetch products from WooCommerce

        Args:
            limit: Maximum number of products

        Returns:
            List of WooCommerce product dictionaries
        """
        products = []
        page = 1
        per_page = 100

        while True:
            batch = await self.woo_client.get_products(per_page=per_page, page=page)

            if not batch:
                break

            products.extend(batch)

            if limit and len(products) >= limit:
                products = products[:limit]
                break

            if len(batch) < per_page:
                break

            page += 1

        return products

    async def _fetch_odoo_products(self, limit: Optional[int]) -> List[dict]:
        """Fetch products from Odoo

        Args:
            limit: Maximum number of products

        Returns:
            List of Odoo product dictionaries
        """
        products = await self.odoo_client.search_read(
            "product.product",
            domain=[["sale_ok", "=", True]],  # Only products that can be sold
            fields=["name", "default_code", "list_price", "qty_available", "weight"],
            limit=limit,
        )

        return products
