import os
import sys
import time
import subprocess
import requests
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from workers.affiliate_worker.schemas import CatalogProduct, TrendSignal
from workers.affiliate_worker.cloud_adapter import push_catalog, push_content, REQUIRED_DISCLOSURE

def run_integration_test():
    print("=== LIVE ADAPTER INTEGRATION TEST (PC Python Worker -> Node SQLite API) ===")
    
    app_dir = Path(r"C:\Users\Yo\amazon-ui")
    test_port = "3199"
    test_token = "test-secret-worker-token-xyz"
    test_data = "./data/test_integration"
    
    env = os.environ.copy()
    env["PORT"] = test_port
    env["HOST"] = "127.0.0.1"
    env["PUBLIC_BASE_URL"] = f"http://127.0.0.1:{test_port}"
    env["DATA_DIR"] = test_data
    env["WORKER_TOKEN"] = test_token
    env["ADMIN_TOKEN"] = "test-admin-token-123"
    env["AFFILIATE_ALLOWED_HOSTS"] = "www.amazon.com,amazon.com"
    env["FEED_ALLOWED_HOSTS"] = "www.amazon.com,images-na.ssl-images-amazon.com,m.media-amazon.com"
    env["MEDIA_ALLOWED_HOSTS"] = "images-na.ssl-images-amazon.com,jyrqzjctkmzdvmraqrcv.supabase.co"
    env["AUTOMATION_ENABLED"] = "false"
    
    print(f"[1/4] Starting isolated Node server on port {test_port}...")
    server_proc = subprocess.Popen(
        ["node", "server/index.js"],
        cwd=str(app_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to be ready
    health_url = f"http://127.0.0.1:{test_port}/api/health"
    ready = False
    for i in range(15):
        try:
            r = requests.get(health_url, timeout=1)
            if r.status_code == 200:
                ready = True
                print(" -> Node server is ready and responding at", health_url)
                break
        except Exception:
            time.sleep(0.5)
            
    if not ready:
        server_proc.kill()
        out, err = server_proc.communicate()
        print("Server failed to start:", out, err)
        sys.exit(1)
        
    try:
        # Configure adapter env variables
        os.environ["PUBLIC_BASE_URL"] = f"http://127.0.0.1:{test_port}"
        os.environ["WORKER_TOKEN"] = test_token
        
        # 2. Test /api/worker/catalog
        print("\n[2/4] Testing POST /api/worker/catalog from Python adapter...")
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        sample_signal = TrendSignal(
            platform="google_trends",
            source_url="https://trends.google.com/trending/rss?geo=US",
            current_count=5000,
            previous_count=1000,
            observed_at=now_iso,
            metric="searches_24h"
        )
        sample_prod = CatalogProduct(
            external_id="pc_worker_test_prod_001",
            title="Minimalist Mechanical Keyboard 75%",
            description="Compact wireless mechanical keyboard with hot-swappable switches and PBT keycaps.",
            category="Tech & gadgets",
            merchant="Amazon",
            affiliate_url="https://www.amazon.com/dp/B0KEYBOARD",
            image_url="https://images-na.ssl-images-amazon.com/images/I/keyboard.jpg",
            price=79.99,
            price_checked_at=now_iso,
            currency="USD",
            affiliate_verified=False,
            media_rights=False,
            search_terms=["mechanical keyboard", "custom keyboard"],
            signals=[sample_signal]
        )
        
        cat_result = push_catalog([sample_prod])
        print(" -> Catalog push result:", cat_result)
        assert cat_result.get("status") == "success", f"Catalog push failed: {cat_result}"
        
        # 3. Query the product to verify insertion and obtain uuid
        import sqlite3
        db_path = app_dir / "data" / "test_integration" / "pulpo.sqlite"
        conn = sqlite3.connect(str(db_path))
        row = conn.execute("SELECT id, external_id, title, score, status FROM products WHERE external_id=?", ("pc_worker_test_prod_001",)).fetchone()
        print(" -> SQLite DB record created:", row)
        assert row is not None, "Product was not found in SQLite DB!"
        product_uuid = row[0]
        
        # Set status='published', affiliate_verified=1, media_rights=1 to enable content creation
        conn.execute("UPDATE products SET status='published', affiliate_verified=1, media_rights=1 WHERE id=?", (product_uuid,))
        conn.commit()
        print(f" -> Updated product {product_uuid} to verified published status for content testing.")
        
        # 4. Test /api/worker/content
        print("\n[3/4] Testing POST /api/worker/content from Python adapter...")
        content_result = push_content(
            product_id=product_uuid,
            kind="reel",
            media_url="https://jyrqzjctkmzdvmraqrcv.supabase.co/storage/v1/object/public/reels-output/reels/test_reel_001.mp4",
            caption="Clean ergonomic setup with tactile typing experience. Link in bio.",
            external_id="content_render_job_001"
        )
        print(" -> Content push result:", content_result)
        assert content_result.get("status") == "success", f"Content push failed: {content_result}"
        
        job_row = conn.execute("SELECT id, product_id, kind, status, caption, media_url FROM jobs WHERE product_id=?", (product_uuid,)).fetchone()
        print(" -> SQLite DB Job created:", job_row)
        assert job_row is not None, "Job was not found in SQLite DB!"
        assert job_row[3] == "draft", f"Job status should be draft, got {job_row[3]}"
        assert job_row[4].startswith(REQUIRED_DISCLOSURE), "Job caption does not start with disclosure!"
        
        # Test deduplication
        print("\n[4/4] Testing deduplication on /api/worker/content...")
        dup_result = push_content(
            product_id=product_uuid,
            kind="reel",
            media_url="https://jyrqzjctkmzdvmraqrcv.supabase.co/storage/v1/object/public/reels-output/reels/test_reel_001.mp4",
            caption="Clean ergonomic setup with tactile typing experience. Link in bio.",
            external_id="content_render_job_001"
        )
        print(" -> Deduplication result:", dup_result)
        assert dup_result.get("response", {}).get("duplicate") is True, f"Expected duplicate=True, got {dup_result}"
        
        print("\n>>> ALL LOCAL INTEGRATION CHECKS PASSED WITH 100% SUCCESS! <<<")
        
    finally:
        print("\nStopping Node server...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except Exception:
            server_proc.kill()
        print("Cleaned up Node server process.")

if __name__ == "__main__":
    run_integration_test()
