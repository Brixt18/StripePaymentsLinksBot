from typing import Any

import stripe


class StripeSDK:
    def __init__(self, api_key: str):
        stripe.api_key = api_key

    def _paginate(self, query: Any) -> list[dict[str, Any]]:
        data = [item for item in query['data']]

        while query.has_more:
            query = query.next_page()
            data.extend([item for item in query['data']])

        return data

    def get_existing_products(self, *args, **kwargs) -> list[dict[str, Any]]:
        query = stripe.Product.list(*args, **kwargs)

        return self._paginate(query)

    def get_existing_prices(self, product_id: str, active: bool | None = True, **kwargs) -> list[dict[str, Any]]:
        query = stripe.Price.list(
            product=product_id,
            active=active,
            **kwargs
        )

        return self._paginate(query)
