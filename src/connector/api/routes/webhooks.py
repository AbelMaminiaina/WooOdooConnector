from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
from loguru import logger

from ...infrastructure.woocommerce import WooCommerceClient
from ...infrastructure.odoo import OdooClient
from ...application.sync_orders import SyncOrdersUseCase
from ...application.sync_stock import SyncStockUseCase
from ...config import settings


router = APIRouter()


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


@router.post("/woocommerce/order")
async def woocommerce_order_webhook(
    request: Request, x_wc_webhook_topic: Optional[str] = Header(None)
):
    """Handle WooCommerce order webhooks

    WooCommerce sends webhooks for various order events:
    - order.created
    - order.updated
    - order.deleted

    Configure this in WooCommerce: Settings > Advanced > Webhooks
    """
    try:
        # Get webhook payload
        payload = await request.json()
        order_id = payload.get("id")

        logger.info(
            f"Received WooCommerce webhook: {x_wc_webhook_topic} for order {order_id}"
        )

        # Handle different webhook topics
        if x_wc_webhook_topic in ["order.created", "order.updated"]:
            # Sync the order to Odoo
            woo_client, odoo_client = get_clients()

            async with woo_client, odoo_client:
                # Get the full order data
                order_data = await woo_client.get_order(order_id)

                # Sync to Odoo
                use_case = SyncOrdersUseCase(woo_client, odoo_client)
                await use_case._sync_single_order(order_data)

            logger.info(f"Successfully processed order webhook for order {order_id}")

            return {"success": True, "message": f"Order {order_id} synced to Odoo"}

        elif x_wc_webhook_topic == "order.deleted":
            logger.info(f"Order {order_id} deleted in WooCommerce")
            # Handle order deletion if needed
            return {"success": True, "message": f"Order {order_id} deletion noted"}

        return {"success": True, "message": "Webhook received"}

    except Exception as e:
        logger.error(f"Error processing WooCommerce webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/woocommerce/product")
async def woocommerce_product_webhook(
    request: Request, x_wc_webhook_topic: Optional[str] = Header(None)
):
    """Handle WooCommerce product webhooks

    WooCommerce sends webhooks for various product events:
    - product.created
    - product.updated
    - product.deleted
    """
    try:
        payload = await request.json()
        product_id = payload.get("id")

        logger.info(
            f"Received WooCommerce webhook: {x_wc_webhook_topic} for product {product_id}"
        )

        # Here you would implement product sync logic
        # Similar to order webhooks

        return {
            "success": True,
            "message": f"Product webhook received for product {product_id}",
        }

    except Exception as e:
        logger.error(f"Error processing WooCommerce webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/odoo/stock")
async def odoo_stock_webhook(request: Request):
    """Handle Odoo stock update webhooks

    This endpoint can be called from Odoo when stock levels change.
    You would need to configure an automation in Odoo to call this endpoint.
    """
    try:
        payload = await request.json()
        sku = payload.get("sku")
        quantity = payload.get("quantity")

        logger.info(f"Received Odoo stock webhook for SKU {sku}: {quantity}")

        if not sku:
            raise HTTPException(status_code=400, detail="SKU is required")

        # Update stock in WooCommerce
        woo_client, odoo_client = get_clients()

        async with woo_client, odoo_client:
            use_case = SyncStockUseCase(woo_client, odoo_client)
            results = await use_case.execute(sku=sku)

        return {
            "success": True,
            "message": f"Stock updated for SKU {sku}",
            "results": results,
        }

    except Exception as e:
        logger.error(f"Error processing Odoo webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_webhook():
    """Test endpoint to verify webhooks are working"""
    return {"status": "ok", "message": "Webhook endpoint is working"}
