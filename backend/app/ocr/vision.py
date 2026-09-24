"""Vision-based price extraction for flyers that arrive as a photo/graphic
image rather than a scrapeable web page (shop.smk.kr flyers are handled by
app.scrapers.smk instead - this is the fallback for everything else).

Traditional OCR (Tesseract etc.) struggles here: these flyers mix product
photos, discount badges, gradient backgrounds and wildly different font
sizes with no consistent grid to key off of. Claude's vision + a forced
tool call gets structured (name, option, price, original_price) data
directly instead of raw text that would still need to be re-parsed.
"""

import base64
from dataclasses import dataclass

import anthropic

from app.config import settings

MODEL = "claude-sonnet-5"

_TOOL = {
    "name": "record_flyer_items",
    "description": "Record every product price shown in the flyer image.",
    "input_schema": {
        "type": "object",
        "properties": {
            "store_name": {
                "type": ["string", "null"],
                "description": "The mart/store name printed on the flyer, if visible in this image. Null if not shown.",
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "option": {"type": "string"},
                        "price": {"type": "integer"},
                        "original_price": {"type": ["integer", "null"]},
                        "note": {"type": ["string", "null"]},
                    },
                    "required": ["name", "option", "price", "original_price", "note"],
                },
            },
        },
        "required": ["items"],
    },
}

_PROMPT = """This is a Korean grocery/mart flyer image. Extract every product and its
price into the record_flyer_items tool call. One visual price tag can cover
several real items - split those into separate entries rather than losing
information. Watch for these patterns:

1. Plain single item: one product, one price -> one entry, original_price null.

2. Genuine discount: two prices on the same single product, where one is
   visually de-emphasized (struck through, smaller, greyed out) as the "was"
   price and the other is highlighted as the current price -> one entry,
   "price" = the highlighted/current price, "original_price" = the other one.

3. Several DIFFERENT products sharing one price tag via "/", e.g. product
   text "안성탕면(125gx5입)/올리브짜파게티(140gx5입)" with price text
   "3,300원/4,700원" -> split into separate entries, matching each name to
   the price in the same position (안성탕면 -> 3300, 올리브짜파게티 -> 4700).
   original_price null for both.

4. Several SIZES/VARIANTS of one product listed with "/", e.g. option
   "800g/1.5kg" with price "6,384원/9,520원" -> split into separate entries,
   one per size, each with its own option and price. original_price null.

5. "각 N원" (each N won) next to a list of products/variants -> one entry
   per listed product/variant, all with price = N, original_price null.

6. A price tag with wording like "즉시할인 2,000원 적용가 9,490원" where only
   the final price is a number and no separate original price number is
   shown -> "price" = 9490, "original_price" = null, and put the discount
   wording verbatim in "note" (e.g. "즉시할인 2,000원 적용가") so it isn't lost.
   Do NOT compute original_price yourself from the discount wording - only
   fill it in when an actual pre-discount price number is printed.

General field rules:
- "price" is the actual selling price (KRW) as a plain integer - no commas, no "원".
- "option" is the unit/weight/origin/quantity text printed with the product
  (e.g. "국산·2kg·BOX", "1단", "450g·봉"). Use "" if none is shown.
- "note" carries any other short qualifier printed near the price that
  doesn't fit "option" (discount wording, "토/일/월 3일간" limited-day
  labels, etc). null if there's nothing like that.
- Skip banner/decorative text, dates, store hours, and anything without an
  actual price next to it.
- If the store name is printed on the flyer, put it in "store_name",
  otherwise null.
"""


@dataclass
class OcrItem:
    name: str
    option: str
    price: int
    original_price: int | None
    note: str | None


@dataclass
class OcrResult:
    store_name: str | None
    items: list[OcrItem]


def extract_flyer_items(image_bytes: bytes, media_type: str = "image/jpeg") -> OcrResult:
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Copy backend/.env.example to backend/.env "
            "and fill in an Anthropic API key from https://console.anthropic.com/"
        )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    b64 = base64.standard_b64encode(image_bytes).decode()

    response = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "record_flyer_items"},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": b64},
                    },
                    {"type": "text", "text": _PROMPT},
                ],
            }
        ],
    )

    tool_use = next(b for b in response.content if b.type == "tool_use")
    data = tool_use.input
    items = [
        OcrItem(
            name=it["name"].strip(),
            option=(it.get("option") or "").strip(),
            price=it["price"],
            original_price=it.get("original_price"),
            note=it.get("note"),
        )
        for it in data.get("items", [])
    ]
    return OcrResult(store_name=data.get("store_name"), items=items)
