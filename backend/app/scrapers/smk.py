"""Scraper for shop.smk.kr flyer pages (e.g. 광장식자재마트's daily KakaoTalk flyer link).

The flyer page itself renders client-side: it loads a near-empty HTML shell,
then calls two internal JSON endpoints to fill in categories and items. We
replicate those two calls instead of OCRing the rendered page, which is far
more reliable than parsing an image/screenshot.

Flow:
1. GET the flyer HTML and pull out `shopid`, the numeric `pId`, and the
   `type` token that the page's own JS passes to categorylist.php (this
   token is baked into the HTML at render time, not computed client-side,
   so it has to be re-scraped from the page each time rather than hardcoded).
2. POST categorylist.php -> [{cId, sub}], the category tabs (사과/야채/정육/...).
3. POST itemlist.php per cId -> the products in that category. Despite the
   field names, `price` is the actual selling price and `nprice` (when
   present and nonzero) is the pre-discount original price shown struck
   through next to it - confirmed by cross-checking against the rendered
   page, e.g. "11,000 9,900" renders from {"price": "9900", "nprice": "11000"}.
"""

import re
from dataclasses import dataclass, field

import httpx

BASE = "https://shop.smk.kr/managerplus/include"

_SHOPID_RE = re.compile(r"var shopid\s*=\s*'([^']+)'")
_CATLIST_CALL_RE = re.compile(
    r"categorylist\.php.{0,300}?pId:\s*['\"]?(\d+)['\"]?.{0,200}?type:\s*['\"]([0-9a-f]+)['\"]",
    re.S,
)
_MART_NAME_RE = re.compile(r'<h1 class="logo[^"]*">\s*<a[^>]*>\s*([^<]+?)\s*</a>', re.S)
_PHONE_RE = re.compile(r'class="martTell">([^<]+)')
_ADDRESS_RE = re.compile(r'class="martAddr">([^<]+)')


@dataclass
class FlyerItem:
    category: str
    name: str
    option: str
    price: int
    original_price: int | None


@dataclass
class FlyerResult:
    mart_name: str
    shopid: str
    phone: str | None
    address: str | None
    items: list[FlyerItem] = field(default_factory=list)


def _to_price(raw: str) -> int | None:
    raw = (raw or "").strip()
    if not raw or raw == "0":
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def scrape_flyer(url: str, timeout: float = 20.0) -> FlyerResult:
    with httpx.Client(timeout=timeout) as client:
        html = client.get(url).text

        shopid_match = _SHOPID_RE.search(html)
        catlist_match = _CATLIST_CALL_RE.search(html)
        if not shopid_match or not catlist_match:
            raise ValueError(
                "Could not find shopid / categorylist.php token in the flyer page. "
                "The page template may have changed."
            )
        shopid = shopid_match.group(1)
        pid, token = catlist_match.group(1), catlist_match.group(2)

        name_match = _MART_NAME_RE.search(html)
        phone_match = _PHONE_RE.search(html)
        address_match = _ADDRESS_RE.search(html)

        categories = client.post(
            f"{BASE}/categorylist.php", data={"pId": pid, "type": token}
        ).json()

        items: list[FlyerItem] = []
        for cat in categories:
            cid, name = cat["cId"], cat["sub"].strip()
            try:
                raw_items = client.post(
                    f"{BASE}/itemlist.php", data={"pname": cid, "type": 3}
                ).json()
            except (httpx.HTTPError, ValueError):
                continue
            if not isinstance(raw_items, list):
                continue
            for raw in raw_items:
                price = _to_price(raw.get("price", ""))
                if price is None:
                    continue
                items.append(
                    FlyerItem(
                        category=name,
                        name=raw.get("iname", "").strip(),
                        option=raw.get("ioption", "").strip(),
                        price=price,
                        original_price=_to_price(raw.get("nprice", "")),
                    )
                )

        return FlyerResult(
            mart_name=name_match.group(1).strip() if name_match else shopid,
            shopid=shopid,
            phone=phone_match.group(1).strip() if phone_match else None,
            address=address_match.group(1).strip() if address_match else None,
            items=items,
        )
