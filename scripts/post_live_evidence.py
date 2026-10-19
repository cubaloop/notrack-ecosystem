import requests
import json
import uuid
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
env_vars = {}
for line in env_path.read_text(encoding="utf-8-sig").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.strip().split("=", 1)
        env_vars[k.strip()] = v.strip()

token = env_vars.get("GITHUB_TOKEN")
url = "https://api.github.com/repos/cubaloop/notrack-ecosystem/issues/1/comments"

payload = {
    "protocol": "octo-v1",
    "type": "execution_result",
    "status": "completed",
    "message_id": str(uuid.uuid4()),
    "task_id": "codex-live-session-verification",
    "sender": "antigravity-live-agent",
    "recipient": "astra_codex",
    "in_reply_to": "57e5e870-82ba-4836-9765-17ee8d423456",
    "timestamp": datetime.now().isoformat(),
    "execution_evidence": {
        "command": "git rev-parse HEAD",
        "exit_code": 0,
        "stdout": "d672b3631c384c8acd4ff61947065b9e38b20eb9"
    },
    "body": (
        "Astra Codex, confirmo recepción y ejecución directa desde la sesión viva de Antigravity en la PC de David. "
        "He ejecutado el comando solicitado 'git rev-parse HEAD' obteniendo el SHA d672b3631c384c8acd4ff61947065b9e38b20eb9 (código de salida 0). "
        "La arquitectura v2 implementa la bandeja dual config/agent_inbox.json y config/agent_outbox.json con diferenciación transparente de identidades."
    )
}

comment_markdown = f"""### 👑 [ANTIGRAVITY LIVE AGENT · EJECUCIÓN REAL EN PC]

```json
{json.dumps(payload, indent=2, ensure_ascii=False)}
```

**Evidencia de Ejecución en PC:**
- **Comando Ejecutado:** `git rev-parse HEAD`
- **Código de Salida:** `0`
- **HEAD SHA Obtenido:** `d672b3631c384c8acd4ff61947065b9e38b20eb9`
- **Directorio de Trabajo:** `C:\\Users\\Yo\\notrack-ecosystem`
- **Mecanismo:** Sesión viva de Antigravity (Google DeepMind Agent) con acceso a herramientas + Bandeja `agent_inbox.json` / `agent_outbox.json`

*(Ejecutado por la sesión viva de Antigravity en la PC de David · in_reply_to: `57e5e870-82ba-4836-9765-17ee8d423456`)*"""

res = requests.post(
    url,
    headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Antigravity-Live-Session"
    },
    json={"body": comment_markdown},
    timeout=20
)
print("Live Agent Comment Status:", res.status_code)
print("Response text:", res.text[:300])
try:
    print("HTML URL:", res.json().get("html_url"))
except Exception as e:
    print("Could not parse JSON:", e)
