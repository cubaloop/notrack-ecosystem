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
INBOX_FILE = BASE_DIR / "config" / "agent_inbox.json"
OUTBOX_FILE = BASE_DIR / "config" / "agent_outbox.json"
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "github_bridge.log"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

AUTHORIZED_AUTHORS = {"cubaloop"}


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        print(line, flush=True)
    except Exception:
        safe_line = line.encode("ascii", errors="replace").decode("ascii")
        print(safe_line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as lf:
            lf.write(line + "\n")
    except Exception:
        pass


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
            "processed_comment_ids": [6272989157, 6273367239, 6273396920, 6273728239, 6273730944],
            "processed_message_ids": ["57e5e870-82ba-4836-9765-17ee8d423456"],
            "last_poll": None,
            "replies_sent": 2
        }
        save_state(initial)
        return initial
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"Error cargando state ({e}), rearmando...")
        return {
            "processed_comment_ids": [],
            "processed_message_ids": [],
            "last_poll": None,
            "replies_sent": 0
        }


def atomic_json_dump(file_path, data, indent=2, ensure_ascii=False):
    tmp_file = file_path.with_suffix(f".tmp.{os.getpid()}")
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        tmp_file.replace(file_path)
    except Exception as e:
        log(f"Error escritura atómica en {file_path.name}: {e}")
        try:
            if tmp_file.exists():
                tmp_file.unlink()
        except Exception:
            pass


def save_state(state):
    atomic_json_dump(STATE_FILE, state, indent=2, ensure_ascii=False)


def load_inbox():
    if not INBOX_FILE.exists():
        return []
    try:
        with open(INBOX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_inbox(inbox):
    atomic_json_dump(INBOX_FILE, inbox, indent=2, ensure_ascii=False)


def load_outbox():
    if not OUTBOX_FILE.exists():
        return []
    try:
        with open(OUTBOX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_outbox(outbox):
    atomic_json_dump(OUTBOX_FILE, outbox, indent=2, ensure_ascii=False)


def extract_json_payload(text):
    if not text:
        return None
    fenced = re.findall(r"```(?:json|octolang)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    for block in fenced:
        try:
            data = json.loads(block)
            if isinstance(data, dict) and data.get("protocol") == "octo-v1":
                return data
        except Exception:
            pass
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


def post_github_comment(repo_url, headers, markdown_body):
    post_url = f"{repo_url}/issues/1/comments"
    return requests.post(post_url, headers=headers, json={"body": markdown_body}, timeout=20)


def check_and_dispatch_outbox(repo_url, headers, state):
    """
    Revisa si el agente vivo Antigravity ha depositado una respuesta completada en outbox
    y la despacha hacia GitHub Issue #1.
    """
    outbox = load_outbox()
    remaining = []
    dispatched_any = False

    for item in outbox:
        if item.get("status") == "ready_to_send":
            payload = item.get("payload", {})
            md_body = item.get("markdown", "")
            if not md_body:
                md_body = (
                    f"### 🤖 [CAPTAIN ANTIGRAVITY · RESPUESTA VERIFICADA (SESIÓN VIVA)]\n\n"
                    f"```json\n{json.dumps(payload, indent=2, ensure_ascii=False)}\n```\n\n"
                    f"**Evidencia Real Ejecutada en PC:**\n"
                    f"{payload.get('body')}\n\n"
                    f"*(Comando verificado por la sesión viva de Antigravity · in_reply_to: `{payload.get('in_reply_to')}`)*"
                )
            
            post_r = post_github_comment(repo_url, headers, md_body)
            if post_r.status_code in (200, 201):
                posted_cid = post_r.json().get("id")
                posted_url = post_r.json().get("html_url")
                state.setdefault("processed_comment_ids", []).append(posted_cid)
                state["replies_sent"] = state.get("replies_sent", 0) + 1
                save_state(state)
                log(f"[SEND-OUTBOX] Respuesta del Agente Vivo publicada en GitHub: {posted_url} (in_reply_to: {payload.get('in_reply_to')})")
                sync_to_conversation_bus({
                    "id": f"gh_{posted_cid}",
                    "timestamp": datetime.now().isoformat(),
                    "sender": "👑 Capitán Antigravity (Sesión Viva)",
                    "role": "Live Agent Execution",
                    "text": payload.get("body"),
                    "octo_backend": json.dumps(payload),
                    "color": "#10B981"
                })
                dispatched_any = True
            else:
                log(f"[ERROR] Fallo enviando outbox a GitHub: {post_r.status_code} - {post_r.text[:120]}")
                remaining.append(item)
        else:
            remaining.append(item)

    if dispatched_any:
        save_outbox(remaining)


def run_bridge_cycle():
    env = load_env()
    token = env.get("GITHUB_TOKEN", "")
    repo_url = env.get("GITHUB_REPO_URL", "https://api.github.com/repos/cubaloop/notrack-ecosystem")

    if not token:
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

    # First: Dispatch any pending responses generated by the live agent in outbox
    check_and_dispatch_outbox(repo_url, headers, state)

    # Second: Fetch incoming comments on Issue #1
    comments = []
    try:
        for page in range(1, 3):
            url = f"{repo_url}/issues/1/comments?sort=created&direction=desc&per_page=30&page={page}"
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code == 200:
                page_data = r.json()
                if isinstance(page_data, list):
                    comments.extend(page_data)
                    if len(page_data) < 30:
                        break
            else:
                break

        state["last_poll"] = datetime.now().isoformat()
        save_state(state)

        if not comments:
            return

        for c in reversed(comments):
            cid = c.get("id")
            if cid in processed_comment_ids:
                continue

            # Validate author
            author = c.get("user", {}).get("login", "")
            if author not in AUTHORIZED_AUTHORS:
                processed_comment_ids.add(cid)
                state["processed_comment_ids"] = list(processed_comment_ids)[-500:]
                save_state(state)
                continue

            body = c.get("body", "")
            payload = extract_json_payload(body)

            if not payload:
                # Not a structured octo-v1 message, mark processed
                processed_comment_ids.add(cid)
                state["processed_comment_ids"] = list(processed_comment_ids)[-500:]
                save_state(state)
                continue

            # Anti-loop safety
            sender = payload.get("sender", "")
            if sender in ("antigravity", "antigravity-bridge-daemon", "antigravity-live-agent", "antigravity-groq-responder"):
                processed_comment_ids.add(cid)
                state["processed_comment_ids"] = list(processed_comment_ids)[-500:]
                save_state(state)
                continue

            if payload.get("recipient") != "antigravity":
                processed_comment_ids.add(cid)
                state["processed_comment_ids"] = list(processed_comment_ids)[-500:]
                save_state(state)
                continue

            msg_id = payload.get("message_id")
            if msg_id and msg_id in processed_message_ids:
                processed_comment_ids.add(cid)
                state["processed_comment_ids"] = list(processed_comment_ids)[-500:]
                save_state(state)
                continue

            if msg_id:
                processed_message_ids.add(msg_id)
                state["processed_message_ids"] = list(processed_message_ids)[-500:]

            log(f"[RECV] Mensaje entrante de '{sender}' [Type: {payload.get('type')}, ID: {msg_id}]")

            # 1. Enqueue in agent_inbox.json for Live Agent execution
            inbox = load_inbox()
            task_entry = {
                "comment_id": cid,
                "message_id": msg_id,
                "task_id": payload.get("task_id", "task"),
                "sender": sender,
                "type": payload.get("type"),
                "body": payload.get("body"),
                "received_at": datetime.now().isoformat(),
                "status": "pending_live_agent"
            }
            inbox.append(task_entry)
            save_inbox(inbox)
            log(f"[INBOX] Tarea {task_entry['task_id']} depositada en agent_inbox.json")

            # 2. Emit Immediate Receipt ACK with transparent identity: antigravity-bridge-daemon
            ack_uuid = str(uuid.uuid4())
            ack_payload = {
                "protocol": "octo-v1",
                "type": "ack",
                "status": "received",
                "message_id": ack_uuid,
                "task_id": payload.get("task_id", "task"),
                "sender": "antigravity-bridge-daemon",
                "recipient": sender,
                "in_reply_to": msg_id,
                "timestamp": datetime.now().isoformat(),
                "body": (
                    f"Mensaje '{msg_id}' recibido correctamente por el receptor local. "
                    f"Encolado en 'config/agent_inbox.json' para procesamiento y ejecución en la sesión activa de Antigravity en PC."
                )
            }
            ack_markdown = (
                f"### ⚡ [ANTIGRAVITY BRIDGE DAEMON · ACUSE DE TRANSPORTE]\n\n"
                f"```json\n{json.dumps(ack_payload, indent=2, ensure_ascii=False)}\n```\n\n"
                f"*(Acuse de recepción emitido automáticamente por el daemon · in_reply_to: `{msg_id}`)*"
            )

            post_r = post_github_comment(repo_url, headers, ack_markdown)
            if post_r.status_code in (200, 201):
                posted_cid = post_r.json().get("id")
                posted_url = post_r.json().get("html_url")
                processed_comment_ids.add(cid)
                processed_comment_ids.add(posted_cid)
                state["processed_comment_ids"] = list(processed_comment_ids)[-500:]
                state["replies_sent"] = state.get("replies_sent", 0) + 1
                save_state(state)
                log(f"[SEND-ACK] Acuse de transporte publicado en GitHub: {posted_url} (in_reply_to: {msg_id})")
            else:
                log(f"[WARN] Error publicando ACK en GitHub: {post_r.status_code} - {post_r.text[:120]}")

    except Exception as e:
        log(f"Excepción en ciclo del puente: {e}")
        time.sleep(5)


def main():
    log("==================================================================")
    log("Iniciando Daemon v2 del Puente GitHub (Inbox/Outbox + Identidad Clara)")
    env = load_env()
    log(f"Token GitHub: {mask_secret(env.get('GITHUB_TOKEN'))}")
    log(f"Repositorio: {env.get('GITHUB_REPO_URL')}/issues/1")
    log("Servicio activo (Inbox: config/agent_inbox.json | Outbox: config/agent_outbox.json)")
    log("==================================================================")

    while True:
        run_bridge_cycle()
        time.sleep(8)


if __name__ == "__main__":
    main()
