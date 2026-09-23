from fastapi import APIRouter

from app.mock_data import MARKETS, PRICES, PRODUCTS

router = APIRouter()


@router.get("/products")
def list_products():
    """Each product with its price at every market."""
    markets_by_id = {m["id"]: m["name"] for m in MARKETS}
    result = []
    for product in PRODUCTS:
        offers = [
            {
                "market_id": p["market_id"],
                "market_name": markets_by_id[p["market_id"]],
                "price": p["price"],
            }
            for p in PRICES
            if p["product_id"] == product["id"]
        ]
        result.append({**product, "offers": sorted(offers, key=lambda o: o["price"])})
    return result


@router.get("/lowest-price")
def lowest_price():
    """The cheapest market for each product."""
    markets_by_id = {m["id"]: m["name"] for m in MARKETS}
    result = []
    for product in PRODUCTS:
        offers = [p for p in PRICES if p["product_id"] == product["id"]]
        if not offers:
            continue
        cheapest = min(offers, key=lambda o: o["price"])
        result.append(
            {
                "product_id": product["id"],
                "product_name": product["name"],
                "market_id": cheapest["market_id"],
                "market_name": markets_by_id[cheapest["market_id"]],
                "price": cheapest["price"],
            }
        )
    return result
