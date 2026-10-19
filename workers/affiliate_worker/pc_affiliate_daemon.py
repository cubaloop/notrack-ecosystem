"""
PC Affiliate Worker Daemon:
Monitors trend feeds, prepares product sync payloads, and maintains local state
without interfering with cloud infrastructure or amazon-ui.
"""
import time
import json
from pathlib import Path
from datetime import datetime
from .trend_monitor import fetch_daily_trends
from .schemas import TrendItem

WORKER_DIR = Path(__file__).resolve().parent
STATE_FILE = WORKER_DIR / "worker_state.json"


def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_trend_sync": None, "known_trends": [], "products_ready": []}


def save_state(state):
    tmp_path = STATE_FILE.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    tmp_path.replace(STATE_FILE)


def run_cycle():
    state = load_state()
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    # Poll trends for UAE (AE) and Global (US)
    trends_ae = fetch_daily_trends("AE")
    time.sleep(1)
    trends_us = fetch_daily_trends("US")
    
    combined = {t.keyword: t.to_dict() for t in trends_ae + trends_us}
    state["known_trends"] = list(combined.values())
    state["last_trend_sync"] = now_str
    save_state(state)
    print(f"[{now_str}] Sync complete: {len(combined)} active trends indexed.")


if __name__ == "__main__":
    print("Starting PC Affiliate Worker cycle...")
    run_cycle()
