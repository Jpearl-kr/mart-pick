from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query

from app.database import get_supabase
from app.scrapers.smk import scrape_flyer

router = APIRouter(prefix="/scrape", tags=["scrape"])


@router.get("/smk")
def scrape_smk_flyer(url: str = Query(..., description="shop.smk.kr flyer URL")):
    """Preview what a shop.smk.kr flyer link (the kind sent over KakaoTalk) scrapes to.

    Doesn't write to the DB - this is for checking the scrape looks right
    before ingesting it.
    """
    try:
        result = scrape_flyer(url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return asdict(result)


@router.post("/smk/ingest")
def ingest_smk_flyer(url: str = Query(..., description="shop.smk.kr flyer URL")):
    """Scrape a flyer and upsert it into Supabase (markets + price_snapshots).

    Safe to call again for the same market on the same day - rows are
    upserted on (market, date, item_name, item_option), so a re-run just
    updates prices instead of duplicating rows.
    """
    try:
        result = scrape_flyer(url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        sb = get_supabase()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    market = (
        sb.table("markets")
        .upsert(
            {
                "name": result.mart_name,
                "source_type": "smk_kakao_flyer",
                "source_key": result.shopid,
                "phone": result.phone,
                "address": result.address,
            },
            on_conflict="source_type,source_key",
        )
        .execute()
    )
    market_id = market.data[0]["id"]

    rows = [
        {
            "market_id": market_id,
            "category": item.category,
            "item_name": item.name,
            "item_option": item.option,
            "price": item.price,
            "original_price": item.original_price,
        }
        for item in result.items
    ]
    if rows:
        sb.table("price_snapshots").upsert(
            rows, on_conflict="market_id,scraped_at,item_name,item_option"
        ).execute()

    return {"market_id": market_id, "market_name": result.mart_name, "items_ingested": len(rows)}
