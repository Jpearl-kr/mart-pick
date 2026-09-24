from dataclasses import asdict

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.database import get_supabase
from app.ocr.vision import extract_flyer_items

router = APIRouter(prefix="/ocr", tags=["ocr"])


@router.post("/flyer")
async def ocr_flyer(file: UploadFile = File(...)):
    """Preview what a photographed/graphic flyer image extracts to.

    Doesn't write to the DB - for checking the extraction looks right first.
    """
    image_bytes = await file.read()
    try:
        result = extract_flyer_items(image_bytes, media_type=file.content_type or "image/jpeg")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return asdict(result)


@router.post("/flyer/ingest")
async def ingest_ocr_flyer(
    market_name: str = Query(..., description="Which market this flyer is for"),
    file: UploadFile = File(...),
):
    """OCR a flyer image and upsert it into Supabase (markets + price_snapshots).

    Unlike the smk scraper there's no stable per-market id to key off of, so
    the market is identified by the `market_name` you pass in.
    """
    image_bytes = await file.read()
    try:
        result = extract_flyer_items(image_bytes, media_type=file.content_type or "image/jpeg")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    try:
        sb = get_supabase()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    market = (
        sb.table("markets")
        .upsert(
            {"name": market_name, "source_type": "ocr", "source_key": market_name},
            on_conflict="source_type,source_key",
        )
        .execute()
    )
    market_id = market.data[0]["id"]

    rows = [
        {
            "market_id": market_id,
            "item_name": item.name,
            "item_option": item.option,
            "price": item.price,
            "original_price": item.original_price,
            "note": item.note,
        }
        for item in result.items
    ]
    if rows:
        sb.table("price_snapshots").upsert(
            rows, on_conflict="market_id,scraped_at,item_name,item_option"
        ).execute()

    return {"market_id": market_id, "market_name": market_name, "items_ingested": len(rows)}
