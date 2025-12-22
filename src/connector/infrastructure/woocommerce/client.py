from typing import Any, Dict, List, Optional
import httpx
from loguru import logger
import base64


class WooCommerceClient:
    """Client for WooCommerce REST API

    This client uses WooCommerce's official REST API.
    Completely independent - no GPL/AGPL concerns.
    """

    def __init__(self, url: str, consumer_key: str, consumer_secret: str):
        """Initialize WooCommerce client

        Args:
            url: WooCommerce shop URL (e.g., https://shop.com)
            consumer_key: WooCommerce API consumer key
            consumer_secret: WooCommerce API consumer secret
        """
        self.url = url.rstrip("/")
        self.api_url = f"{self.url}/wp-json/wc/v3"
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

        # Create basic auth header
        credentials = f"{consumer_key}:{consumer_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/json",
            },
        )

    async def get_orders(
        self,
        status: Optional[str] = None,
        per_page: int = 100,
        page: int = 1,
        after: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get orders from WooCommerce

        Args:
            status: Order status filter (processing, completed, etc.)
            per_page: Number of orders per page (max 100)
            page: Page number
            after: Get orders after this date (ISO8601 format)

        Returns:
            List of order dictionaries
        """
        params = {"per_page": min(per_page, 100), "page": page}

        if status:
            params["status"] = status
        if after:
            params["after"] = after

        response = await self._get("orders", params)
        logger.info(f"Retrieved {len(response)} orders from WooCommerce")
        return response

    async def get_order(self, order_id: int) -> Dict[str, Any]:
        """Get a single order by ID

        Args:
            order_id: WooCommerce order ID

        Returns:
            Order dictionary
        """
        response = await self._get(f"orders/{order_id}")
        logger.info(f"Retrieved order {order_id} from WooCommerce")
        return response

    async def update_order(self, order_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an order

        Args:
            order_id: WooCommerce order ID
            data: Order data to update

        Returns:
            Updated order dictionary
        """
        response = await self._put(f"orders/{order_id}", data)
        logger.info(f"Updated order {order_id} in WooCommerce")
        return response

    async def get_products(
        self,
        per_page: int = 100,
        page: int = 1,
        sku: Optional[str] = None,
        status: str = "publish",
    ) -> List[Dict[str, Any]]:
        """Get products from WooCommerce

        Args:
            per_page: Number of products per page (max 100)
            page: Page number
            sku: Filter by SKU
            status: Product status (publish, draft, pending)

        Returns:
            List of product dictionaries
        """
        params = {"per_page": min(per_page, 100), "page": page, "status": status}

        if sku:
            params["sku"] = sku

        response = await self._get("products", params)
        logger.info(f"Retrieved {len(response)} products from WooCommerce")
        return response

    async def get_product(self, product_id: int) -> Dict[str, Any]:
        """Get a single product by ID

        Args:
            product_id: WooCommerce product ID

        Returns:
            Product dictionary
        """
        response = await self._get(f"products/{product_id}")
        logger.info(f"Retrieved product {product_id} from WooCommerce")
        return response

    async def update_product(
        self, product_id: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a product

        Args:
            product_id: WooCommerce product ID
            data: Product data to update

        Returns:
            Updated product dictionary
        """
        response = await self._put(f"products/{product_id}", data)
        logger.info(f"Updated product {product_id} in WooCommerce")
        return response

    async def update_product_stock(
        self, product_id: int, quantity: int
    ) -> Dict[str, Any]:
        """Update product stock quantity

        Args:
            product_id: WooCommerce product ID
            quantity: New stock quantity

        Returns:
            Updated product dictionary
        """
        data = {
            "stock_quantity": quantity,
            "manage_stock": True,
            "stock_status": "instock" if quantity > 0 else "outofstock",
        }
        return await self.update_product(product_id, data)

    async def get_customers(
        self, per_page: int = 100, page: int = 1, email: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get customers from WooCommerce

        Args:
            per_page: Number of customers per page (max 100)
            page: Page number
            email: Filter by email

        Returns:
            List of customer dictionaries
        """
        params = {"per_page": min(per_page, 100), "page": page}

        if email:
            params["email"] = email

        response = await self._get("customers", params)
        logger.info(f"Retrieved {len(response)} customers from WooCommerce")
        return response

    async def _get(self, endpoint: str, params: Dict = None) -> Any:
        """Make GET request to WooCommerce API

        Args:
            endpoint: API endpoint (e.g., 'orders', 'products/123')
            params: Query parameters

        Returns:
            Response JSON data
        """
        url = f"{self.api_url}/{endpoint}"

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"WooCommerce GET error on {endpoint}: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    async def _post(self, endpoint: str, data: Dict) -> Any:
        """Make POST request to WooCommerce API

        Args:
            endpoint: API endpoint
            data: Request body data

        Returns:
            Response JSON data
        """
        url = f"{self.api_url}/{endpoint}"

        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"WooCommerce POST error on {endpoint}: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    async def _put(self, endpoint: str, data: Dict) -> Any:
        """Make PUT request to WooCommerce API

        Args:
            endpoint: API endpoint
            data: Request body data

        Returns:
            Response JSON data
        """
        url = f"{self.api_url}/{endpoint}"

        try:
            response = await self.client.put(url, json=data)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"WooCommerce PUT error on {endpoint}: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
