"""AIHOT scraper — fetch AI news from aiHOT public API (free, no auth).
Returns ContentItem-compatible dicts so they blend seamlessly into Horizon's pipeline.
"""
import json, urllib.request
from datetime import datetime, UTC, timedelta
from typing import List


AIHOT_API = "https://aihot.virxact.com/api/public/items"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def fetch_aihot_items(take: int = 30) -> List[dict]:
    """Fetch selected (curated) AI news items from aiHOT.
    Returns list of Horizon-compatible content dicts.
    """
    since = (datetime.now(UTC) - timedelta(hours=36)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"{AIHOT_API}?mode=selected&since={since}&take={take}"

    req = urllib.request.Request(url)
    req.add_header("User-Agent", UA)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"    Warning: aiHOT API failed ({e})")
        return []

    items = data.get("items", data.get("data", []))
    if isinstance(items, dict):
        items = list(items.values())
    if not isinstance(items, list):
        return []

    results = []
    for item in items:
        if not isinstance(item, dict):
            continue
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "summary": item.get("summary", item.get("title", "")),
            "score": float(item.get("score", item.get("rating", 5))),
            "tags": [item.get("category", "AI")],
            "source": "aiHOT",
            "fetched_at": datetime.now(UTC).isoformat(),
        })

    print(f"    [aiHOT] {len(results)} curated AI items fetched")
    return results
