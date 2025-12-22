import json
from typing import Any, Dict, List, Optional
import httpx
from loguru import logger


class OdooClient:
    """Client for Odoo JSON-RPC API

    This client communicates with Odoo using its public JSON-RPC API.
    No AGPL code is used - only API calls to external service.
    """

    def __init__(self, url: str, db: str, username: str, password: str):
        """Initialize Odoo client

        Args:
            url: Odoo instance URL (e.g., https://your-odoo.com)
            db: Database name
            username: Odoo username
            password: Odoo password
        """
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password
        self.uid: Optional[int] = None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def authenticate(self) -> int:
        """Authenticate with Odoo and get user ID

        Returns:
            User ID (uid)

        Raises:
            Exception: If authentication fails
        """
        try:
            response = await self._call(
                service="common",
                method="login",
                args=[self.db, self.username, self.password]
            )

            if not response:
                raise Exception("Authentication failed: Invalid credentials")

            self.uid = response
            logger.info(f"Authenticated with Odoo as user {self.username} (uid: {self.uid})")
            return self.uid

        except Exception as e:
            logger.error(f"Odoo authentication error: {e}")
            raise

    async def create(self, model: str, values: Dict[str, Any]) -> int:
        """Create a record in Odoo

        Args:
            model: Odoo model name (e.g., 'sale.order', 'product.product')
            values: Dictionary of field values

        Returns:
            Created record ID
        """
        if not self.uid:
            await self.authenticate()

        result = await self._execute(model, "create", [values])
        logger.info(f"Created {model} with ID {result}")
        return result

    async def write(self, model: str, record_ids: List[int], values: Dict[str, Any]) -> bool:
        """Update record(s) in Odoo

        Args:
            model: Odoo model name
            record_ids: List of record IDs to update
            values: Dictionary of field values to update

        Returns:
            True if successful
        """
        if not self.uid:
            await self.authenticate()

        result = await self._execute(model, "write", [record_ids, values])
        logger.info(f"Updated {model} records {record_ids}")
        return result

    async def search_read(
        self,
        model: str,
        domain: List = None,
        fields: List[str] = None,
        limit: int = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Search and read records from Odoo

        Args:
            model: Odoo model name
            domain: Search domain (Odoo format)
            fields: List of fields to retrieve
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of record dictionaries
        """
        if not self.uid:
            await self.authenticate()

        domain = domain or []
        fields = fields or []

        kwargs = {"fields": fields, "offset": offset}
        if limit:
            kwargs["limit"] = limit

        result = await self._execute(
            model,
            "search_read",
            [domain],
            kwargs
        )

        logger.info(f"Found {len(result)} {model} records")
        return result

    async def search(self, model: str, domain: List = None, limit: int = None) -> List[int]:
        """Search for record IDs in Odoo

        Args:
            model: Odoo model name
            domain: Search domain (Odoo format)
            limit: Maximum number of IDs

        Returns:
            List of record IDs
        """
        if not self.uid:
            await self.authenticate()

        domain = domain or []
        args = [domain]

        kwargs = {}
        if limit:
            kwargs["limit"] = limit

        result = await self._execute(model, "search", args, kwargs)
        return result

    async def _execute(
        self,
        model: str,
        method: str,
        args: List = None,
        kwargs: Dict = None
    ) -> Any:
        """Execute a method on an Odoo model

        Args:
            model: Odoo model name
            method: Method name to execute
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Method result
        """
        args = args or []
        kwargs = kwargs or {}

        return await self._call(
            service="object",
            method="execute_kw",
            args=[
                self.db,
                self.uid,
                self.password,
                model,
                method,
                args,
                kwargs
            ]
        )

    async def _call(self, service: str, method: str, args: List) -> Any:
        """Make JSON-RPC call to Odoo

        Args:
            service: Service name ('common' or 'object')
            method: Method name
            args: Method arguments

        Returns:
            JSON-RPC result

        Raises:
            Exception: If request fails
        """
        url = f"{self.url}/jsonrpc"

        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": service,
                "method": method,
                "args": args
            },
            "id": 1
        }

        try:
            response = await self.client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                error_msg = data["error"].get("data", {}).get("message", str(data["error"]))
                raise Exception(f"Odoo error: {error_msg}")

            return data.get("result")

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Odoo: {e}")
            raise
        except Exception as e:
            logger.error(f"Error calling Odoo: {e}")
            raise

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry"""
        await self.authenticate()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
