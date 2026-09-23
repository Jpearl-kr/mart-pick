"""Temporary fake data so the API works before Supabase tables are populated.

Once real `markets` / `products` / `prices` tables exist in Supabase, the
routers in app/routers should read from `app.database.get_supabase()`
instead of this module.
"""

MARKETS = [
    {"id": 1, "name": "영천 하나로마트"},
    {"id": 2, "name": "영천 이마트"},
    {"id": 3, "name": "영천 농협마트"},
]

PRODUCTS = [
    {"id": 1, "name": "계란 30구", "unit": "판"},
    {"id": 2, "name": "우유 1L", "unit": "개"},
    {"id": 3, "name": "쌀 10kg", "unit": "포"},
]

PRICES = [
    {"market_id": 1, "product_id": 1, "price": 7200},
    {"market_id": 2, "product_id": 1, "price": 6900},
    {"market_id": 3, "product_id": 1, "price": 7500},
    {"market_id": 1, "product_id": 2, "price": 2800},
    {"market_id": 2, "product_id": 2, "price": 2950},
    {"market_id": 3, "product_id": 2, "price": 2700},
    {"market_id": 1, "product_id": 3, "price": 32000},
    {"market_id": 2, "product_id": 3, "price": 31500},
    {"market_id": 3, "product_id": 3, "price": 33000},
]
