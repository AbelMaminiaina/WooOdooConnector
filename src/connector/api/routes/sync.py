from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ...infrastructure.woocommerce import WooCommerceClient
from ...infrastructure.odoo import OdooClient
from ...application.sync_orders import SyncOrdersUseCase
from ...application.sync_products import SyncProductsUseCase
from ...application.sync_stock import SyncStockUseCase
from ...config import settings


router = APIRouter()


class SyncResponse(BaseModel):
    """Response model for sync operations"""

    success: bool
    message: str
    results: dict


def get_clients():
    """Get WooCommerce and Odoo clients"""
    woo_client = WooCommerceClient(
        url=settings.woo_url,
        consumer_key=settings.woo_consumer_key,
        consumer_secret=settings.woo_consumer_secret,
    )

    odoo_client = OdooClient(
        url=settings.odoo_url,
        db=settings.odoo_db,
        username=settings.odoo_username,
        password=settings.odoo_password,
    )

    return woo_client, odoo_client


@router.post("/orders", response_model=SyncResponse)
async def sync_orders(
    status: Optional[str] = Query(
        None, description="Order status filter (processing, completed, etc.)"
    ),
    since_days: Optional[int] = Query(
        None, description="Only sync orders from last N days"
    ),
    limit: Optional[int] = Query(None, description="Maximum number of orders to sync"),
):
    """Sync orders from WooCommerce to Odoo

    This endpoint fetches orders from WooCommerce and creates/updates them in Odoo.
    """
    try:
        woo_client, odoo_client = get_clients()

        since = None
        if since_days:
            from datetime import timedelta

            since = datetime.now() - timedelta(days=since_days)

        async with woo_client, odoo_client:
            use_case = SyncOrdersUseCase(woo_client, odoo_client)
            results = await use_case.execute(status=status, since=since, limit=limit)

        return SyncResponse(
            success=results["failed"] == 0,
            message=f"Synced {results['success']} orders successfully",
            results=results,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products/woo-to-odoo", response_model=SyncResponse)
async def sync_products_woo_to_odoo(
    limit: Optional[int] = Query(None, description="Maximum number of products to sync")
):
    """Sync products from WooCommerce to Odoo

    This endpoint fetches products from WooCommerce and creates/updates them in Odoo.
    """
    try:
        woo_client, odoo_client = get_clients()

        async with woo_client, odoo_client:
            use_case = SyncProductsUseCase(woo_client, odoo_client)
            results = await use_case.sync_from_woo_to_odoo(limit=limit)

        return SyncResponse(
            success=results["failed"] == 0,
            message=f"Synced products: {results['created']} created, {results['updated']} updated",
            results=results,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products/odoo-to-woo", response_model=SyncResponse)
async def sync_products_odoo_to_woo(
    limit: Optional[int] = Query(None, description="Maximum number of products to sync")
):
    """Sync products from Odoo to WooCommerce

    This endpoint fetches products from Odoo and updates them in WooCommerce.
    """
    try:
        woo_client, odoo_client = get_clients()

        async with woo_client, odoo_client:
            use_case = SyncProductsUseCase(woo_client, odoo_client)
            results = await use_case.sync_from_odoo_to_woo(limit=limit)

        return SyncResponse(
            success=results["failed"] == 0,
            message=f"Synced {results['updated']} products",
            results=results,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stock", response_model=SyncResponse)
async def sync_stock(
    sku: Optional[str] = Query(None, description="SKU of product to sync (optional)")
):
    """Sync stock levels from Odoo to WooCommerce

    This endpoint updates WooCommerce product stock quantities based on Odoo inventory.
    If SKU is provided, only that product is synced. Otherwise, all products are synced.
    """
    try:
        woo_client, odoo_client = get_clients()

        async with woo_client, odoo_client:
            use_case = SyncStockUseCase(woo_client, odoo_client)
            results = await use_case.execute(sku=sku)

        return SyncResponse(
            success=results["failed"] == 0,
            message=f"Updated stock for {results['success']} products",
            results=results,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def sync_status():
    """Get synchronization status"""
    return {
        "woo_url": settings.woo_url,
        "odoo_url": settings.odoo_url,
        "sync_enabled": settings.sync_enabled,
        "sync_interval_minutes": settings.sync_interval_minutes,
    }
