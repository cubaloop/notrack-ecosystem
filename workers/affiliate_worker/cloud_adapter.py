"""
Cloud Adapter for Affiliate Commerce Platform:
Implements the exact HTTP contract for syncing products to the Cloud API.
Endpoint: POST {PUBLIC_BASE_URL}/api/worker/catalog
Authorization: Bearer {WORKER_TOKEN}
"""
import os
import json
import requests
from typing import List, Dict, Any, Tuple
from pathlib import Path
from dotenv import load_dotenv

from .schemas import CatalogProduct, ALLOWED_CATEGORIES, ALLOWED_METRICS

# Load environment
ENV_FILE = Path(__file__).resolve().parent / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()


def get_config() -> Tuple[str, str]:
    """
    Returns (PUBLIC_BASE_URL, WORKER_TOKEN) safely from local environment.
    """
    base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    token = os.getenv("WORKER_TOKEN", "")
    return base_url, token


def validate_product(prod: CatalogProduct) -> Tuple[bool, str]:
    """
    Ensures a CatalogProduct strictly meets Astra Codex's contract rules.
    """
    if prod.category not in ALLOWED_CATEGORIES:
        return False, f"Category '{prod.category}' not in {ALLOWED_CATEGORIES}"
    
    if prod.currency != "USD":
        return False, f"Currency must be 'USD', got '{prod.currency}'"
        
    for s in prod.signals:
        sig_dict = s.to_dict() if hasattr(s, "to_dict") else s
        metric = sig_dict.get("metric")
        if metric not in ALLOWED_METRICS:
            return False, f"Signal metric '{metric}' not in {ALLOWED_METRICS}"
            
    return True, "OK"


def build_catalog_payload(products: List[CatalogProduct]) -> Dict[str, Any]:
    """
    Builds the exact JSON payload required by the cloud API.
    """
    valid_products = []
    for p in products:
        is_valid, reason = validate_product(p)
        if not is_valid:
            print(f"[Warning] Skipping invalid product {p.external_id}: {reason}")
            continue
        valid_products.append(p.to_dict())
        
    return {"products": valid_products}


def push_catalog(products: List[CatalogProduct], dry_run: bool = False) -> Dict[str, Any]:
    """
    Pushes products to the Cloud endpoint. If dry_run=True, validates and returns payload.
    """
    payload = build_catalog_payload(products)
    
    if dry_run:
        return {
            "status": "dry_run_success",
            "count": len(payload["products"]),
            "payload_sample": payload["products"][:2] if payload["products"] else []
        }
        
    base_url, token = get_config()
    if not base_url or not token:
        return {
            "status": "skipped_missing_credentials",
            "message": "PUBLIC_BASE_URL or WORKER_TOKEN not set in local environment."
        }
        
    target_url = f"{base_url}/api/worker/catalog"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.post(target_url, json=payload, headers=headers, timeout=25)
        return {
            "status": "success" if resp.status_code in (200, 201) else "error",
            "status_code": resp.status_code,
            "response": resp.text[:200]
        }
    except Exception as e:
        return {"status": "connection_error", "error": str(e)}


if __name__ == "__main__":
    from datetime import datetime
    from .schemas import TrendSignal
    
    sample_signal = TrendSignal(
        platform="google_trends",
        source_url="https://trends.google.com/trending/rss?geo=US",
        current_count=5000,
        previous_count=0,
        observed_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        metric="searches_24h"
    )
    
    sample_product = CatalogProduct(
        external_id="ext_desk_lamp_001",
        title="Minimalist LED Desk Lamp with USB Charging",
        description="Modern dimmable desk lamp with aluminum finish and eye-caring LED array.",
        category="Tech & gadgets",
        merchant="Amazon",
        affiliate_url="https://www.amazon.com/dp/B0EXAMPLE",
        image_url="https://images-na.ssl-images-amazon.com/images/I/sample.jpg",
        price=None,
        currency="USD",
        affiliate_verified=False,
        media_rights=False,
        search_terms=["desk lamp", "led lamp", "office setup"],
        signals=[sample_signal]
    )
    
    res = push_catalog([sample_product], dry_run=True)
    print("Cloud Adapter Dry Run Result:")
    print(json.dumps(res, indent=2))
