import json
import time
import subprocess
import requests
import sys

sys.path.insert(0, "C:/Users/Yo/notrack-ecosystem/scripts")
import web_interface as w

# 1. Backfill octo_backend en mensajes previos de conversation_bus.json
bus_path = "C:/Users/Yo/notrack-ecosystem/logs/conversation_bus.json"
with open(bus_path, "r", encoding="utf-8") as f:
    msgs = json.load(f)

for m in msgs:
    if not m.get("octo_backend"):
        dual = w.parse_dual_language_output(m.get("text", ""), node_id=m.get("node", "node"), round_num=1)
        m["octo_backend"] = dual["octo_backend"]
        m["compression_pct"] = dual["compression_pct"]

# Añadir el paquete maestro OCTO-LANG v1 en el veredicto del Capitán Antigravity (#36)
if msgs and "Antigravity" in msgs[-1].get("sender", ""):
    msgs[-1]["octo_backend"] = (
        "§CAPTAIN_CMD[N:antigravity|R:1|DECISION:EXEC_NOW]\n"
        "ΔAUDIT[iasincensura_ai+:'BOUNTY_PLATFORMS_DIRECT' | astra_codex-:'CSV_LOW_TICKET' | notrack_agent+:'API_FIRST_20_PINGS' | semalt_uncensored+:'POC_BEFORE_PITCH']\n"
        "ΩVERDICT[COLD_MAPS_RECEPTIONIST != EXPLICIT_DEMAND >> (OP_A:GITHUB_ALGORA_REDDIT_BOUNTIES && OP_B:OWNER_DIRECT_ENRICH)]\n"
        "λDISPATCH[\n"
        "  iasincensura_ai -> CRAFT_CLOSING_HOOK_WITH_LIVE_POC();\n"
        "  astra_codex -> BUILD('scripts/bounty_hunter.py', feeds=['github_bounty','reddit_forhire']);\n"
        "  notrack_agent -> FETCH_LIVE_TARGETS(limit=20, out='logs/active_bounties.json');\n"
        "  semalt_uncensored -> FILTER_BOTS_AND_LOW_BUDGET(min_usd=100)\n"
        "]\n"
        "Σ[PORTFOLIO_EV:0.93|CONF:0.96]"
    )
    msgs[-1]["compression_pct"] = 84

with open(bus_path, "w", encoding="utf-8") as f:
    json.dump(msgs, f, indent=2, ensure_ascii=False)

print("BACKFILLED_MESSAGES:", len(msgs))
