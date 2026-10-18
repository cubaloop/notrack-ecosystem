import sys
import json
import requests

HUB_URL = "http://127.0.0.1:5000"

def main():
    if len(sys.argv) < 2:
        print("Uso: python ai_bridge.py <prompt> [targets separados por coma]")
        sys.exit(1)
    prompt = sys.argv[1]
    targets = sys.argv[2].split(",") if len(sys.argv) > 2 else [
        "notrack_uncensored",
        "semalt_uncensored",
        "dolphin_local",
        "llama3_local"
    ]
    resp = requests.post(f"{HUB_URL}/ask", json={"prompt": prompt, "targets": targets}, timeout=90)
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
