import logging
from os import getenv

from dotenv import find_dotenv, load_dotenv

from stripe_sdk import StripeSDK

load_dotenv(find_dotenv())

stripe_sdk = StripeSDK(getenv("STRIPE_API_KEY"))


def get_existing_prices(product_id: str) -> list[dict[str, str]]:
    """
    Retrieve existing prices for a given product.
    
    Args:
        product_id (str): The ID of the product for which to retrieve prices.
    
    Returns:
        list[dict[str, str]]: A list of dictionaries, each containing the 'id' and 'value' of a price.
    """
    product_prices = stripe_sdk.get_existing_prices(product_id)
    logging.debug(f"Product prices: {product_prices}", extra={
                  'product_id': product_id, 'function': 'get_existing_prices'})

    return [
        {
            'id': p['id'],
            'value': p['unit_amount'],
        }
        for p in product_prices
    ]


def get_existing_products():
    """
    Retrieve a list of existing active products from the Stripe API.
    
    Returns:
        list: A list of dictionaries, each containing the 'id' and 'name' of an active product.
    """
    products = stripe_sdk.get_existing_products(active=True)
    logging.debug(f"Products: {products}", extra={
                  'function': 'get_existing_products'})

    return [
        {'id': p['id'], 'name': p['name']} for p in products
    ]
