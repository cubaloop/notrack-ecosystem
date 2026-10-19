"""
Data schemas for the Affiliate Commerce Worker.
Matches the exact contract specified by Astra Codex for cloud sync.
"""
from dataclasses import dataclass, asdict, field
from typing import List, Optional


ALLOWED_CATEGORIES = [
    "Home & living",
    "Tech & gadgets",
    "Everyday carry",
    "Kitchen",
    "Wellness"
]

ALLOWED_METRICS = [
    "views_7d",
    "searches_7d",
    "sales_7d",
    "engagements_7d",
    "searches_24h"
]


@dataclass
class TrendSignal:
    platform: str
    source_url: str
    current_count: int
    previous_count: int
    observed_at: str  # ISO 8601
    metric: str  # views_7d | searches_7d | sales_7d | engagements_7d | searches_24h

    def to_dict(self):
        return asdict(self)


@dataclass
class CatalogProduct:
    external_id: str
    title: str
    description: str
    category: str
    merchant: str
    affiliate_url: str
    image_url: str
    video_url: Optional[str] = None
    price: Optional[float] = None
    currency: str = "USD"
    price_checked_at: Optional[str] = None
    affiliate_verified: bool = False
    media_rights: bool = False
    search_terms: List[str] = field(default_factory=list)
    signals: List[TrendSignal] = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        d["signals"] = [s.to_dict() if isinstance(s, TrendSignal) else s for s in self.signals]
        return d
