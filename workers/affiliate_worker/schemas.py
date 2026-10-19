"""
Data schemas for the Affiliate Commerce Worker.
Maintains strict type consistency between PC worker and Cloud components.
"""
from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class TrendItem:
    trend_id: str
    keyword: str
    category: str
    volume_score: int
    region: str
    source: str
    detected_at: str

    def to_dict(self):
        return asdict(self)


@dataclass
class AffiliateProduct:
    sku: str
    title: str
    category: str
    price_aed: float
    price_usd: float
    affiliate_url: str
    original_url: str
    image_url: str
    rating: float
    review_count: int
    trend_score: float
    in_stock: bool
    last_updated: str

    def to_dict(self):
        return asdict(self)


@dataclass
class SocialCreative:
    creative_id: str
    product_sku: str
    hook: str
    caption: str
    hashtags: List[str]
    affiliate_disclosure: str
    image_path: Optional[str]
    status: str  # draft, ready, published
    created_at: str

    def to_dict(self):
        return asdict(self)
