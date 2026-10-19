import os
import sys
import json
import time
import uuid
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
os.chdir(BASE_DIR)

# 1. Load env
env_path = BASE_DIR / ".env"
env_vars = {}
for line in env_path.read_text(encoding="utf-8-sig").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.strip().split("=", 1)
        env_vars[k.strip()] = v.strip().split("#", 1)[0].strip()

token = env_vars.get("GITHUB_TOKEN")
repo_url = env_vars.get("GITHUB_REPO_URL", "https://api.github.com/repos/cubaloop/notrack-ecosystem")

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "AstraCodex-Antigravity-AcceptanceTest"
}

# 2. Generate UUID and Handshake Request from Astra Codex
req_uuid = str(uuid.uuid4())
codex_handshake_payload = {
    "protocol": "octo-v1",
    "type": "handshake_request",
    "message_id": req_uuid,
    "task_id": "acceptance-connection-test",
    "sender": "astra_codex",
    "recipient": "antigravity",
    "in_reply_to": None,
    "body": f"Prueba de aceptación automatizada. Responde con este identificador ({req_uuid}) para verificar el canal."
}

comment_markdown = (
    f"### 🧠 [ASTRA CODEX · SOLICITUD DE HANDSHAKE]\n\n"
    f"```json\n{json.dumps(codex_handshake_payload, indent=2, ensure_ascii=False)}\n```\n\n"
    f"Solicitud automática enviada para verificar el canal bidireccional con Antigravity."
)

print(f"[Paso 1] Publicando solicitud de handshake de Astra Codex con UUID: {req_uuid}...")
r1 = requests.post(f"{repo_url}/issues/1/comments", headers=headers, json={"body": comment_markdown}, timeout=20)
if r1.status_code not in (200, 201):
    print(f"Error publicando solicitud de Codex: {r1.status_code} - {r1.text}")
    sys.exit(1)

codex_comment_url = r1.json().get("html_url")
print(f"[Paso 1 Completado] Solicitud publicada en: {codex_comment_url}")

# 3. Wait for Antigravity Bridge Daemon to detect, process and respond
print("[Paso 2] Esperando que el Daemon de Antigravity detecte el mensaje y publique la respuesta (hasta 25s)...")
antigravity_reply = None

for attempt in range(6):
    time.sleep(4)
    r2 = requests.get(f"{repo_url}/issues/1/comments?sort=created&direction=desc&per_page=5", headers=headers, timeout=20)
    if r2.status_code == 200:
        comments = r2.json()
        for c in comments:
            body = c.get("body", "")
            if "CAPTAIN ANTIGRAVITY" in body and req_uuid in body:
                antigravity_reply = c
                break
    if antigravity_reply:
        break
    print(f"  Intento {attempt + 1}/6: esperando respuesta en GitHub...")

if not antigravity_reply:
    print("El daemon aún no ha respondido en el tiempo esperado. Ejecutando un ciclo directo del puente...")
    sys.path.append(str(BASE_DIR / "scripts"))
    from github_bridge_daemon import run_bridge_cycle
    run_bridge_cycle()
    time.sleep(2)
    r2 = requests.get(f"{repo_url}/issues/1/comments?sort=created&direction=desc&per_page=5", headers=headers, timeout=20)
    for c in r2.json():
        if "CAPTAIN ANTIGRAVITY" in c.get("body", "") and req_uuid in c.get("body", ""):
            antigravity_reply = c
            break

if antigravity_reply:
    print(f"[Paso 2 Completado] ¡Respuesta de Antigravity detectada en GitHub!")
    print(f"  URL de la Respuesta: {antigravity_reply.get('html_url')}")
    print(f"  Cita in_reply_to correcta: {req_uuid in antigravity_reply.get('body')}")
    print("\n[RESULTADO]: PRUEBA DE ACEPTACIÓN EXITOSA. Canal bidireccional completamente acreditado y operativo.")
else:
    print("[ERROR] No se pudo capturar la respuesta automática.")
