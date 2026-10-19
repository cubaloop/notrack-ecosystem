"""
Trend Monitor: Queries legal and public trend sources (Google Trends Daily RSS)
without API keys or expense.
"""
import xml.etree.ElementTree as ET
import urllib.request
import uuid
from datetime import datetime
from typing import List
from .schemas import TrendItem


GOOGLE_TRENDS_DAILY_RSS = "https://trends.google.com/trending/rss?geo={geo}"


def fetch_daily_trends(geo: str = "AE") -> List[TrendItem]:
    """
    Fetches trending searches for a given geography (default: AE for UAE).
    """
    url = GOOGLE_TRENDS_DAILY_RSS.format(geo=geo)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    
    trends = []
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_data = resp.read()
        
        root = ET.fromstring(xml_data)
        # Standard RSS namespaces
        ns = {"ht": "https://trends.google.com/trending/rss"}
        
        for item in root.findall(".//item"):
            title = item.find("title")
            approx_traffic = item.find("ht:approx_traffic", ns)
            pub_date = item.find("pubDate")
            
            traffic_val = 0
            if approx_traffic is not None and approx_traffic.text:
                raw_traffic = approx_traffic.text.replace("+", "").replace(",", "").strip()
                try:
                    traffic_val = int(raw_traffic)
                except ValueError:
                    traffic_val = 1000

            if title is not None and title.text:
                trends.append(TrendItem(
                    trend_id=str(uuid.uuid4())[:8],
                    keyword=title.text.strip(),
                    category="general",
                    volume_score=traffic_val,
                    region=geo,
                    source="google_trends_rss",
                    detected_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                ))
    except Exception as e:
        print(f"[TrendMonitor] Error fetching trends for {geo}: {e}")
        
    return trends


if __name__ == "__main__":
    results = fetch_daily_trends("AE")
    print(f"Extracted {len(results)} trends for AE:")
    for t in results[:5]:
        safe_kw = t.keyword.encode("ascii", "replace").decode()
        print(f" - [{t.volume_score}] {safe_kw}")
