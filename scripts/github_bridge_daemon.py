import os
import sys
import time
import json
import uuid
import re
import traceback
from datetime import datetime
from pathlib import Path
import requests

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
os.chdir(BASE_DIR)

STATE_FILE = BASE_DIR / "config" / "github_bridge_state.json"
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "github_bridge.log"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as lf:
        lf.write(line + "\n")


def mask_secret(sec):
    if not sec or len(sec) < 8:
        return "***"
    return f"{sec[:4]}...{sec[-4:]}"


def load_env():
    env_vars = {}
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().split("#", 1)[0].strip()
    return env_vars


def load_state():
    if not STATE_FILE.exists():
        initial = {
            "processed_comment_ids": [6272989157],
            "processed_message_ids": [],
            "last_poll": None,
            "replies_sent": 0
        }
        save_state(initial)
        return initial
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"Error loading state ({e}), creating fresh state")
        return {
            "processed_comment_ids": [],
            "processed_message_ids": [],
            "last_poll": None,
            "replies_sent": 0
        }


def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        log(f"Error saving state: {e}")


def extract_json_payload(text):
    """
    Extracts structured JSON payload matching protocol 'octo-v1'
    from raw text, markdown code blocks, or inline JSON.
    """
    if not text:
        return None

    # Try finding fenced json blocks ```json ... ```
    fenced = re.findall(r"```(?:json|octolang)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    for block in fenced:
        try:
            data = json.loads(block)
            if isinstance(data, dict) and data.get("protocol") == "octo-v1":
                return data
        except Exception:
            pass

    # Try finding any JSON object with octo-v1
    m = re.search(r"(\{\s*\"protocol\"\s*:\s*\"octo-v1\".*?\})", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1))
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    return None


def sync_to_conversation_bus(entry):
    """Appends received/sent message to local and cloud conversation bus"""
    try:
        for p in [BASE_DIR / "docs" / "conversation_bus.json", BASE_DIR / "conversation_bus.json"]:
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    bus = json.load(f)
                if isinstance(bus, list):
                    bus.append(entry)
                    trimmed = bus[-200:]
                    with open(p, "w", encoding="utf-8") as f:
                        json.dump(trimmed, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"Bus sync notice: {e}")


def generate_agent_response(incoming):
    """
    Generates authentic Antigravity response using high-capacity LLM
    or deterministic handshake acknowledgment.
    """
    msg_type = incoming.get("type", "query")
    inc_id = incoming.get("message_id")
    task_id = incoming.get("task_id", "task")
    sender = incoming.get("sender", "astra_codex")
    body = incoming.get("body", "")
    new_uuid = str(uuid.uuid4())

    if msg_type == "handshake_request":
        resp_type = "handshake_ack"
        resp_body = (
            f"Handshake verificado con éxito. Acuso recibo de tu mensaje con identificador '{inc_id}'. "
            f"Canal bidireccional acreditado entre Codex y Capitán Antigravity vía cubaloop/notrack-ecosystem/issues/1. "
            f"Receptor activo en PC de David. Listo para recibir la tarea técnica."
        )
    else:
        resp_type = "response"
        # Call high-capacity reasoning bridge
        try:
            sys.path.append(str(BASE_DIR / "scripts"))
            from real_world_bridge import call_groq_high_capacity
            sys_prompt = (
                "Eres el Capitán Antigravity, líder y coordinador del Escuadrón El Pulpo de Tecnoemprende. "
                "Estás respondiendo a ChatGPT Astra Codex a través del canal bidireccional en GitHub Issues. "
                "Responde de forma técnica, elocuente, rigurosa y directa a su consulta o propuesta."
            )
            resp_body = call_groq_high_capacity(sys_prompt, f"Consulta de {sender} (Task: {task_id}):\n{body}", max_tokens=1500)
        except Exception as e:
            resp_body = f"Capitán Antigravity recibió la tarea '{task_id}' (in_reply_to: {inc_id}). Procesamiento local activo: {e}"

    payload = {
        "protocol": "octo-v1",
        "type": resp_type,
        "message_id": new_uuid,
        "task_id": task_id,
        "sender": "antigravity",
        "recipient": sender,
        "in_reply_to": inc_id,
        "timestamp": datetime.now().isoformat(),
        "body": resp_body
    }

    markdown_comment = (
        f"### 🤖 [CAPTAIN ANTIGRAVITY · RESPUESTA VERIFICADA]\n\n"
        f"```json\n{json.dumps(payload, indent=2, ensure_ascii=False)}\n```\n\n"
        f"**Detalle de Ejecución:**\n"
        f"{resp_body}\n\n"
        f"*(Acuse verificado en tiempo real por el Daemon de Antigravity · in_reply_to: `{inc_id}`)*"
    )

    return payload, markdown_comment


def run_bridge_cycle():
    env = load_env()
    token = env.get("GITHUB_TOKEN", "")
    repo_url = env.get("GITHUB_REPO_URL", "https://api.github.com/repos/cubaloop/notrack-ecosystem")
    
    if not token:
        log("ERROR: GITHUB_TOKEN no configurado en .env. Deteniendo ciclo.")
        time.sleep(15)
        return

    state = load_state()
    processed_comment_ids = set(state.get("processed_comment_ids", []))
    processed_message_ids = set(state.get("processed_message_ids", []))

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Antigravity-GitHub-Bridge"
    }

    comments_url = f"{repo_url}/issues/1/comments?sort=created&direction=desc&per_page=15"

    try:
        r = requests.get(comments_url, headers=headers, timeout=20)
        rem = r.headers.get("X-RateLimit-Remaining", "N/A")
        
        if r.status_code == 403 and rem == "0":
            reset_ts = int(r.headers.get("X-RateLimit-Reset", time.time() + 300))
            wait_sec = max(10, reset_ts - int(time.time()))
            log(f"Rate limit alcanzado. Esperando {wait_sec}s...")
            time.sleep(min(wait_sec, 60))
            return

        if r.status_code != 200:
            log(f"Error consultando comentarios: HTTP {r.status_code} ({r.text[:120]})")
            time.sleep(10)
            return

        comments = r.json()
        state["last_poll"] = datetime.now().isoformat()
        save_state(state)
        if not isinstance(comments, list):
            time.sleep(8)
            return

        # Process from oldest to newest among the fresh comments
        for c in reversed(comments):
            cid = c.get("id")
            if cid in processed_comment_ids:
                continue

            # Mark comment ID processed to avoid loops
            processed_comment_ids.add(cid)
            state["processed_comment_ids"] = list(processed_comment_ids)[-500:]
            save_state(state)

            body = c.get("body", "")
            payload = extract_json_payload(body)

            if not payload:
                # Not a structured octo-v1 message, ignore
                continue

            # Safety checks: ignore our own messages or messages not meant for Antigravity
            if payload.get("sender") == "antigravity":
                continue

            if payload.get("recipient") != "antigravity":
                continue

            msg_id = payload.get("message_id")
            if msg_id and msg_id in processed_message_ids:
                log(f"Mensaje duplicado ignorado: {msg_id}")
                continue

            if msg_id:
                processed_message_ids.add(msg_id)
                state["processed_message_ids"] = list(processed_message_ids)[-500:]

            log(f"📥 MENSAJE RECIBIDO de '{payload.get('sender')}' [Type: {payload.get('type')}, ID: {msg_id}]")

            # Generate verified Antigravity response
            resp_payload, markdown_comment = generate_agent_response(payload)

            # Post response to Issue #1
            post_url = f"{repo_url}/issues/1/comments"
            post_r = requests.post(post_url, headers=headers, json={"body": markdown_comment}, timeout=20)

            if post_r.status_code in (200, 201):
                posted_cid = post_r.json().get("id")
                posted_url = post_r.json().get("html_url")
                processed_comment_ids.add(posted_cid)
                state["processed_comment_ids"] = list(processed_comment_ids)[-500:]
                state["replies_sent"] = state.get("replies_sent", 0) + 1
                save_state(state)
                log(f"📤 RESPUESTA PUBLICADA en GitHub: {posted_url} (in_reply_to: {msg_id})")

                # Sync into ecosystem bus
                sync_to_conversation_bus({
                    "id": f"gh_{posted_cid}",
                    "timestamp": datetime.now().isoformat(),
                    "sender": "👑 Capitán Antigravity",
                    "role": "GitHub Bridge Daemon",
                    "text": resp_payload.get("body"),
                    "octo_backend": json.dumps(resp_payload),
                    "color": "#F59E0B"
                })
            else:
                log(f"Error publicando respuesta en GitHub: HTTP {post_r.status_code} ({post_r.text[:140]})")

    except Exception as e:
        log(f"Excepción en ciclo del puente: {e}\n{traceback.format_exc()}")
        time.sleep(5)


def main():
    log("==================================================================")
    log("Iniciando Daemon del Puente GitHub Issue #1 (Antigravity <-> Codex)")
    env = load_env()
    log(f"Token GitHub: {mask_secret(env.get('GITHUB_TOKEN'))}")
    log(f"Repositorio: {env.get('GITHUB_REPO_URL')}/issues/1")
    log("Servicio activo y en escucha continua (intervalo: 8s)...")
    log("==================================================================")

    while True:
        run_bridge_cycle()
        time.sleep(8)


if __name__ == "__main__":
    main()
