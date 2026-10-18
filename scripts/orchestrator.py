import os
import sys
import time
import json
import base64
import requests
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
os.chdir(BASE_DIR)

# Cargar variables desde .env si existe
env_path = BASE_DIR / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as ef:
        for line in ef:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.split("#", 1)[0].strip()
            os.environ.setdefault(k.strip(), v)

# Cargar variables de entorno básicas
NOTRACK_URL = os.getenv('NOTRACK_API_URL', 'http://127.0.0.1:3231')
LOCAL_TOKEN = os.getenv('NOTRACK_LOCAL_TOKEN', '')
GITHUB_REPO = os.getenv('GITHUB_REPO_URL', 'https://api.github.com/repos/cubaloop/notrack-ecosystem')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
MODEL_NAME = os.getenv('MODEL_NAME', 'notrack-coder-uncensored')
STATE_FILE = os.getenv('STATE_FILE', './config/state.json')
LOGS_DIR = os.getenv('LOGS_DIR', './logs')
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', 5))


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"executed_ids": []}
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)


def get_orders_from_github():
    """Lee órdenes desde el repositorio de GitHub (commands.json) o fallback local"""
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if GITHUB_TOKEN and not GITHUB_TOKEN.startswith('['):
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    try:
        if GITHUB_REPO and 'TU_USUARIO_GITHUB' not in GITHUB_REPO:
            response = requests.get(f"{GITHUB_REPO}/contents/commands.json", headers=headers, timeout=15)
            if response.status_code == 200:
                content = base64.b64decode(response.json()['content']).decode('utf-8')
                data = json.loads(content)
                if isinstance(data, list):
                    return data
    except Exception as e:
        print(f"[Orchestrator] Error leyendo GitHub: {e}", flush=True)

    # Fallback local opcional en ./config/commands.json
    local_cmds = os.path.join(os.path.dirname(STATE_FILE), "commands.json")
    if os.path.exists(local_cmds):
        try:
            with open(local_cmds, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return []


def parse_notrack_response(resp):
    """Parsea respuesta JSON o stream SSE (data: {...}) del demonio NoTrack Local"""
    try:
        return resp.json()
    except Exception:
        text = resp.text or ""
        events = []
        reply_chunks = []
        conv_id = None
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                raw = line[5:].strip()
                try:
                    ev = json.loads(raw)
                    events.append(ev)
                    if ev.get("conversation_id"):
                        conv_id = ev.get("conversation_id")
                    if ev.get("type") in ("token", "text", "delta", "content") and ev.get("text"):
                        reply_chunks.append(ev.get("text"))
                    elif isinstance(ev.get("delta"), str):
                        reply_chunks.append(ev.get("delta"))
                    elif isinstance(ev.get("content"), str):
                        reply_chunks.append(ev.get("content"))
                except Exception:
                    pass
        return {
            "status_code": resp.status_code,
            "conversation_id": conv_id,
            "reply": "".join(reply_chunks) if reply_chunks else text[:2000],
            "events_count": len(events)
        }


def execute_via_notrack(command_text):
    """Envía la orden al demonio local de NoTrack"""
    payload = {
        "message": command_text,
        "user_input": command_text,
        "endpoint_id": "notrack-uncensored",
        "model": MODEL_NAME,
        "agent": True,
        "approval": "auto",
        "stream": False
    }
    headers = {
        "X-SC-Token": LOCAL_TOKEN,
        "Content-Type": "application/json"
    }

    print(f"[Orchestrator] Enviando orden a NoTrack Local: {command_text[:50]}...", flush=True)
    try:
        resp = requests.post(f"{NOTRACK_URL}/api/chat", json=payload, headers=headers, timeout=120)
        result = parse_notrack_response(resp)

        # Guardar log
        os.makedirs(LOGS_DIR, exist_ok=True)
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command_text,
            "response": result
        }
        log_file = os.path.join(LOGS_DIR, f"log_{int(time.time())}.json")
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)

        return result
    except Exception as e:
        return {"error": str(e)}


def main():
    print("[Orchestrator] Iniciando ciclo de escucha autónoma...", flush=True)
    print(f"[Orchestrator] Conectado a NoTrack Local en {NOTRACK_URL} | Repo: {GITHUB_REPO}", flush=True)
    state = load_state()
    save_state(state)

    while True:
        try:
            # 1. Leer nuevas órdenes (desde GitHub/IA Remota)
            new_orders = get_orders_from_github()

            for order in new_orders:
                order_id = order.get('id')
                command = order.get('command')

                if order_id and order_id not in state['executed_ids']:
                    print(f"[Orchestrator] Nueva orden detectada ID: {order_id}", flush=True)

                    # Ejecutar
                    result = execute_via_notrack(command)

                    # Actualizar estado
                    state['executed_ids'].append(order_id)
                    save_state(state)

        except KeyboardInterrupt:
            print("\n[Orchestrator] Deteniendo servicio...", flush=True)
            break
        except Exception as e:
            print(f"[Orchestrator] Error de ciclo: {e}", flush=True)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
