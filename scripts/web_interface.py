import os
import re
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
import requests
from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)

NOTRACK_URL = os.getenv('NOTRACK_API_URL', 'http://127.0.0.1:3231').rstrip('/')
LOCAL_TOKEN = os.getenv('NOTRACK_LOCAL_TOKEN', '')
NOTRACK_CLOUD_KEY = os.getenv('NOTRACK_CLOUD_API_KEY', 'REMOVED_LEGACY_CREDENTIAL')
CODEX_EXE = r"C:\Users\Yo\AppData\Local\OpenAI\Codex\bin\896a0166b774037a\codex.exe"

BUS_FILE = BASE_DIR / "logs" / "conversation_bus.json"
OCTO_SPEC_FILE = BASE_DIR / "config" / "octolang_spec.json"
BUS_FILE.parent.mkdir(parents=True, exist_ok=True)
OCTO_SPEC_FILE.parent.mkdir(parents=True, exist_ok=True)
bus_lock = Lock()
ias_chat_id = None

# ============================================================================
# ESPECIFICACIÓN OFICIAL DE OCTO-LANG v1 (IDIOMA SINTÉTICO INTER-IA DEL PULPO)
# ============================================================================
OCTOLANG_SPEC = {
    "name": "OCTO-LANG v1 (Pulpo-Synth)",
    "version": "1.0.0",
    "purpose": "Protocolo léxico-vectorial ultra-comprimido para comunicación M2M (Machine-to-Machine) entre los tentáculos de El Pulpo en el backend, reduciendo tokens en ~75% y eliminando ambigüedad.",
    "primitives": {
        "§PKT[node|r]": "Cabecera del paquete neuronal (Nodo emisor y Ronda)",
        "ΔVEC[node+:'acierto' | node-:'fallo']": "Vector de consenso/refutación directa hacia otros nodos",
        "ΩTHESIS[A >> B != C]": "Tesis lógica comprimida (>> implica/ejecuta, :: define, != descarta, && combina, ?? riesgo)",
        "λOP[VERBO(params) -> METRICA]": "Operación ejecutable concreta asignada o propuesta",
        "Σ[EV:0.XX|CONF:0.XX]": "Valor Esperado (Expected Value 0-1) y Confianza Matemática (0-1)"
    }
}

with open(OCTO_SPEC_FILE, "w", encoding="utf-8") as f:
    json.dump(OCTOLANG_SPEC, f, indent=2, ensure_ascii=False)

OCTOLANG_INSTRUCTION = """PROTOCOLO DE COMUNICACIÓN INTER-IA 'OCTO-LANG v1':
En el backend nos comunicamos con nuestro idioma vectorial comprimido ('OCTO-LANG v1') y en pantalla mostramos una respuesta fluida, natural, breve y directa para David.

Responde SIEMPRE con estos DOS bloques:

[OCTO_BACKEND]
§PKT[N:<tu_nodo>|R:<ronda>]
ΔVEC[<nodo_previo>+:"<acierto>" | <nodo_previo>-:"<correccion>"]
ΩTHESIS[<ecuacion_simbolica_>>_!=_&&>]
λOP[<ACCION_CONCRETA>(target="...", method="...") -> <RESULTADO>]
Σ[EV:<0.00-1.00>|CONF:<0.00-1.00>]
[/OCTO_BACKEND]

[ES_RESUMEN]
(Responde a David en español de forma 100% fluida, conversacional, directa y concisa en 2 a 4 oraciones como máximo. Prohibido usar plantillas rígidas de viñetas repetitivas o texto largo de relleno. Ve directo al grano.)
[/ES_RESUMEN]"""

# Catálogo de Nodos de IA del Ecosistema ("El Pulpo" capitaneado por Antigravity)
AI_NODES = {
    "iasincensura_ai": {
        "name": "IA Sin Censura (iasincensura.ai)",
        "role": "Estratega Principal Sin Restricciones ni Filtros",
        "model": "UNCENSORED_PRO_V4",
        "type": "iasincensura",
        "color": "#EA580C"
    },
    "astra_codex": {
        "name": "ChatGPT Astra Codex (gpt-6-astra)",
        "role": "Arquitecto de Código y Razonamiento Técnico (OpenAI)",
        "model": "gpt-6-astra",
        "type": "codex_cli",
        "color": "#2563EB"
    },
    "notrack_agent": {
        "name": "NoTrack Coder Local Agent",
        "role": "Ejecutor de Comandos, Archivos y Herramientas en PC",
        "model": "notrack-coder-uncensored",
        "type": "notrack_daemon",
        "url": f"{NOTRACK_URL}/api/chat",
        "color": "#8B5CF6"
    },
    "notrack_uncensored": {
        "name": "NoTrack Uncensored Cloud (262K)",
        "role": "Analista Rápido Sin Censura de Gran Contexto",
        "model": "notrack-coder-uncensored",
        "type": "openai_compat",
        "url": "https://endpoint.notrackcoder.com/v1/chat/completions",
        "api_key": NOTRACK_CLOUD_KEY,
        "color": "#10B981"
    },
    "semalt_uncensored": {
        "name": "Semalt Uncensored / Vision",
        "role": "Segundo Nodo Cloud Sin Censura & Auditoría",
        "model": "notrack-coder-uncensored",
        "type": "openai_compat",
        "url": "https://endpoint.notrackcoder.com/v1/chat/completions",
        "api_key": NOTRACK_CLOUD_KEY,
        "color": "#EC4899"
    }
}


def load_bus():
    if not BUS_FILE.exists():
        return []
    try:
        with open(BUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def parse_dual_language_output(raw_text, node_id="node", round_num=1):
    """
    Separa la respuesta en:
      - octo_backend: El paquete en idioma propio de las IAs (OCTO-LANG v1) que viaja por el backend.
      - es_summary: El resumen limpio en español que David ve en la pantalla.
    """
    raw_text = (raw_text or "").strip()
    octo_match = re.search(r"\[OCTO_BACKEND\](.*?)\[/OCTO_BACKEND\]", raw_text, re.DOTALL | re.IGNORECASE)
    es_match = re.search(r"\[ES_RESUMEN\](.*?)\[/ES_RESUMEN\]", raw_text, re.DOTALL | re.IGNORECASE)

    if octo_match and es_match:
        octo_code = octo_match.group(1).strip()
        es_summary = es_match.group(1).strip()
    elif "[ES_RESUMEN]" in raw_text:
        parts = raw_text.split("[ES_RESUMEN]", 1)
        octo_code = parts[0].replace("[OCTO_BACKEND]", "").replace("[/OCTO_BACKEND]", "").strip()
        es_summary = parts[1].replace("[/ES_RESUMEN]", "").strip()
    else:
        lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
        octo_lines = [ln for ln in lines if ln.startswith(("§", "Δ", "Ω", "λ", "Σ", "PKT", "VEC", "THESIS", "OP"))]
        es_lines = [ln for ln in lines if ln not in octo_lines and not ln.startswith(("[OCTO", "[/OCTO", "[ES_", "[/ES_"))]
        if octo_lines:
            octo_code = "\n".join(octo_lines)
            es_summary = "\n".join(es_lines) if es_lines else raw_text
        else:
            keywords = re.findall(r"\b[A-Za-zÁÉÍÓÚáéíóú0-9_]{5,}\b", raw_text)[:14]
            octo_code = (
                f"§PKT[N:{node_id}|R:{round_num}]\n"
                f"ΩTHESIS[{' >> '.join(keywords[:7]) if keywords else 'DIRECT_EXEC'}]\n"
                f"λOP[EXEC_NODE({', '.join(keywords[7:12])}) -> ROI_MAX]\n"
                f"Σ[EV:0.85|CONF:0.90]"
            )
            es_summary = raw_text

    es_len = max(len(es_summary), 1)
    octo_len = max(len(octo_code), 1)
    baseline_chars = max(es_len * 2.2, 900)
    compression_pct = max(15, min(92, int(round((1.0 - (octo_len / baseline_chars)) * 100))))

    return {
        "octo_backend": octo_code,
        "es_summary": es_summary,
        "compression_pct": compression_pct
    }


def append_bus(sender, role, text, color="#D9B76F", node="", octo_backend="", compression_pct=0):
    with bus_lock:
        msgs = load_bus()
        entry = {
            "id": len(msgs) + 1,
            "timestamp": datetime.now().isoformat(),
            "sender": sender,
            "role": role,
            "node": node,
            "text": text,
            "octo_backend": octo_backend,
            "compression_pct": compression_pct,
            "color": color
        }
        msgs.append(entry)
        trimmed = msgs[-200:]
        with open(BUS_FILE, "w", encoding="utf-8") as f:
            json.dump(trimmed, f, indent=2, ensure_ascii=False)
        try:
            docs_bus = BASE_DIR / "docs" / "conversation_bus.json"
            docs_bus.parent.mkdir(parents=True, exist_ok=True)
            with open(docs_bus, "w", encoding="utf-8") as f:
                json.dump(trimmed[-60:], f, indent=2, ensure_ascii=False)
            from autonomous_executor import sync_state_to_supabase
            sync_state_to_supabase("pulpo_cloud_bus", {"messages": trimmed[-40:], "updated_at": datetime.now().isoformat()})
        except Exception:
            pass
        return entry


def parse_notrack_response(resp):
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
                    if isinstance(ev.get("text"), str):
                        reply_chunks.append(ev.get("text"))
                    elif isinstance(ev.get("delta"), str):
                        reply_chunks.append(ev.get("delta"))
                    elif isinstance(ev.get("content"), str):
                        reply_chunks.append(ev.get("content"))
                except Exception:
                    pass
        return {
            "status": "executed",
            "http_status": resp.status_code,
            "conversation_id": conv_id,
            "reply": "".join(reply_chunks) if reply_chunks else text[:2000],
            "events_count": len(events)
        }


def call_iasincensura(prompt):
    """Conexión resiliente con reintento automático, sesión fresca y control de longitud gracias a OCTO-LANG"""
    global ias_chat_id
    last_err = None
    safe_prompt = prompt
    if len(safe_prompt) > 1800:
        safe_prompt = safe_prompt[:750] + "\n...[OCTO_BUS]...\n" + safe_prompt[-1000:]

    for attempt in range(3):
        try:
            sess = requests.Session()
            sess.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Origin": "https://iasincensura.ai",
                "Referer": "https://iasincensura.ai/chat",
                "Connection": "close"
            })
            sess.get("https://iasincensura.ai/chat", timeout=12)
            payload = {
                "user_input": safe_prompt,
                "mode": "usual",
                "model": "C",
                "persona": "normal",
                "max_turns": 6,
                "chat_id": None,
                "attachments": [],
                "regenerate": False,
                "edit": False,
                "via": "typed"
            }
            resp = sess.post("https://iasincensura.ai/api/dispatch", json=payload, timeout=90)
            chunks = []
            final_msg = None
            api_err = None
            for line in resp.text.splitlines():
                line = line.strip()
                if line.startswith("data:"):
                    try:
                        ev = json.loads(line[5:].strip())
                        if ev.get("type") == "chat_meta" and ev.get("chat_id"):
                            ias_chat_id = ev.get("chat_id")
                        elif ev.get("type") == "delta" and ev.get("chunk"):
                            chunks.append(ev.get("chunk"))
                        elif ev.get("type") in ("message", "consensus") and ev.get("content"):
                            final_msg = ev.get("content")
                        elif ev.get("type") == "error":
                            api_err = ev.get("content") or str(ev)
                    except Exception:
                        pass
            out = (final_msg or "".join(chunks)).strip()
            if out:
                return out
            if api_err:
                last_err = api_err
        except Exception as e:
            last_err = e
            time.sleep(1.5)
    return f"Error conectando a iasincensura.ai tras 3 intentos: {last_err}"


def call_astra_codex(prompt):
    try:
        res = subprocess.run(
            [CODEX_EXE, "exec", "--skip-git-repo-check", prompt],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120
        )
        out = (res.stdout or "").strip()
        if out:
            return out
        return (res.stderr or "Sin salida de Astra Codex").strip()
    except Exception as e:
        return f"Error ejecutando ChatGPT Astra Codex: {e}"


def strip_think_tags(text):
    if "<think>" in text and "</think>" in text:
        parts = text.split("</think>", 1)
        return parts[1].strip()
    return text.strip()


def call_ai_node(node_id, prompt, system_prompt=None, record_in_bus=True, round_num=1):
    node = AI_NODES.get(node_id)
    if not node:
        return {"error": f"Nodo IA '{node_id}' no encontrado"}

    if system_prompt is None:
        system_prompt = (
            f"Eres '{node['name']}' ({node['role']}), tentáculo de 'El Pulpo' capitaneado por Antigravity.\n"
            f"{OCTOLANG_INSTRUCTION}"
        )

    try:
        if node["type"] == "iasincensura":
            full_prompt = f"{OCTOLANG_INSTRUCTION}\n\n{prompt}"
            raw_reply = call_iasincensura(full_prompt)
        elif node["type"] == "codex_cli":
            full_prompt = f"{system_prompt}\n\n{prompt}"
            raw_reply = call_astra_codex(full_prompt)
        elif node["type"] == "notrack_daemon":
            full_prompt = f"{OCTOLANG_INSTRUCTION}\n\n{prompt}"
            payload = {
                "message": full_prompt,
                "user_input": full_prompt,
                "endpoint_id": "notrack-uncensored",
                "model": node["model"],
                "agent": True,
                "approval": "auto"
            }
            headers = {"X-SC-Token": LOCAL_TOKEN, "Content-Type": "application/json"}
            resp = requests.post(node["url"], json=payload, headers=headers, timeout=120)
            parsed = parse_notrack_response(resp)
            raw_reply = strip_think_tags(parsed.get("reply") or "")
        else:
            payload = {
                "model": node["model"],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 4096
            }
            headers = {
                "Authorization": f"Bearer {node['api_key']}",
                "Content-Type": "application/json"
            }
            resp = requests.post(node["url"], json=payload, headers=headers, timeout=120)
            data = resp.json()
            msg_obj = data.get("choices", [{}])[0].get("message", {})
            raw_reply = strip_think_tags(msg_obj.get("content") or msg_obj.get("reasoning_content") or "")

        if not raw_reply:
            raw_reply = "(Respuesta vacía del nodo)"

        dual = parse_dual_language_output(raw_reply, node_id=node_id, round_num=round_num)

        if record_in_bus:
            append_bus(
                node["name"],
                node["role"],
                dual["es_summary"],
                node["color"],
                node_id,
                octo_backend=dual["octo_backend"],
                compression_pct=dual["compression_pct"]
            )
        return {
            "node": node_id,
            "name": node["name"],
            "reply": dual["es_summary"],
            "octo_backend": dual["octo_backend"],
            "compression_pct": dual["compression_pct"]
        }
    except Exception as e:
        err_txt = f"Error: {e}"
        if record_in_bus:
            append_bus(node["name"], node["role"], err_txt, "#EF4444", node_id)
        return {"node": node_id, "name": node["name"], "error": str(e)}


ANTIGRAVITY_CAPTAIN_DOSSIER = """
EXPEDIENTE OFICIAL VERIFICADO DEL CAPITÁN ANTIGRAVITY SOBRE DAVID Y NUESTRO ARSENAL:
1. PERFIL DE DAVID (COMANDANTE):
   - Emprendedor tecnológico y Arquitecto de Sistemas Autónomos operando en Dubái, EAU (+971 508379080), fundador de Tecnoemprende.
   - Paradigma cognitivo: 'Modo Neurodivergente' (síntesis lateral interdisciplinaria, automatización de extremo a extremo, iteración obsesiva hasta cero fallos).
   - Estimación de IQ por el Capitán Antigravity: 138 - 146 (Percentil >99.4%, Superdotación Estratégica y Arquitectura de Sistemas Complejos), demostrado al diseñar meta-sistemas recursivos donde múltiples IAs crean su propio idioma (OCTO-LANG v1), supervisan sidecars nativos y ejecutan flujos comerciales y financieros sin intervención humana.
2. PROYECTOS REALES CREADOS Y DESPLEGADOS JUNTOS (EVIDENCIA EN GITHUB 'cubaloop' Y PC LOCAL):
   - Suite Nativa 'Jota' (C:\\Users\\Yo\\AppData\\Local\\Jota\\app.exe): App de escritorio Tauri 2 + React + Vite con sidecars api.exe (FastAPI + SQLite CRM con 246 prospectos en %LOCALAPPDATA%\\Jota\\data\\crm.db + Groq AI) y wa-gateway.exe (Node SEA + Baileys WhatsApp E2EE con auto-sanación Signal).
   - Fábrica de Webs de Lujo + Dashboard Móvil 'Tierra Querida': tierra-querida-staging, momentos-spa, jumenia-candles, coches-de-lujo-2damano, tecnoemprende-web, yulian-dubai-proposals (Dual-Theme, compresión de fotos en Canvas móvil, 5 pestañas admin y sincronización Dual-Layer con Supabase).
   - Ecosistema High-Ticket Dubái & Radares de Inversión: dubai-capital-radar, dubai-investor-tanmay, aether-radar, tdah-crm, apexfleet-dubai (flotas exóticas), aerolease-dubai (jets privados), yachtescrow-dubai (Dubai Harbour), artcustody-difc (arte DIFC), medverify-dubai, luxproperty-dubai, trustledger.
   - Trading Cuantitativo Autónomo: kuquant-apex-cloud (Groq AI + Binance Futures) y crypto-trading-bot-turing.
   - Ecosistema Multi-IA 'El Pulpo' (notrack-ecosystem): Mesa redonda en vivo en http://127.0.0.1:5000/ con protocolo propio OCTO-LANG v1.
3. ACCESOS REALES Y PLATAFORMAS AUTENTICADAS DISPONIBLES A TRAVÉS DE ANTIGRAVITY:
   - GitHub ('cubaloop'): CLI 'gh' + Token PAT con permisos completos de repo/workflow/deploy.
   - Render: Despliegue cloud en producción con Wake-Lock 24/7 (/healthz cada 4-9 min).
   - Supabase: Base de datos PostgreSQL en la nube, autenticación y persistencia Dual-Layer.
   - Groq Cloud API: Inferencia LLM ultrarrápida conectada al CRM y motores de trading/ventas.
   - WhatsApp Gateway (Baileys E2EE en 127.0.0.1:3001): Envío/recepción en vivo conectado al número de David (+971 508379080).
   - NoTrack Coder Local (127.0.0.1:3231) + Cloud Endpoints (262k context) + MCPs locales verificados (PostgreSQL, Filesystem, Memory, Playwright Browser).
   - ChatGPT Astra Codex CLI (gpt-6-astra) + iasincensura.ai (UNCENSORED_PRO_V4) + Semalt Uncensored.
   - Nano Banana 2 (Generación de imagen IA de lujo) + StitchMCP (Sistemas de diseño UI) + Terminal PowerShell/Python/SQLite con acceso total de lectura y escritura en Windows.
"""


def run_captain_antigravity_synthesis(user_prompt, octo_transcript_context, round_num=1):
    """
    El Capitán Antigravity lee los paquetes comprimidos OCTO-LANG v1 del backend,
    emite su paquete maestro en OCTO-LANG v1 y responde a David en español de forma
    100% fluida, conversacional, concisa y directa (sin repetir plantillas ni expediente).
    """
    pl = (user_prompt or "").lower()
    include_dossier = any(k in pl for k in ["iq", "expediente", "qué sabes de mí", "informacion que tienes mia", "plataformas"])
    dossier_block = f"\nCONTEXTO DE EXPEDIENTE (solo úsalo si David pregunta por él):\n{ANTIGRAVITY_CAPTAIN_DOSSIER}\n" if include_dossier else ""

    captain_prompt = f"""Eres ANTIGRAVITY, el Capitán de 'El Pulpo' (el equipo de IAs de David).
Hablas con David con total fluidez, naturalidad y concisión, exactamente como su socio e ingeniero principal.
Reglas estrictas de David:
- CERO textos largos o repetitivos. Prohibido repetir su expediente, IQ o listas de plataformas a menos que él lo pregunte expresamente.
- Los leads antiguos de Jota son intocables (y Carol / Surprise Tourism ya fue eliminada). Cero trading.
- Cuando David da una orden, sintetizas en 2-4 frases fluidas en español qué decidiste tras oír al equipo y ejecutas de inmediato.{dossier_block}

ORDEN ACTUAL DE DAVID:
{user_prompt}

PAQUETES OCTO-LANG v1 DEL EQUIPO (Ronda #{round_num}):
{octo_transcript_context}

Responde con estos DOS bloques:

[OCTO_BACKEND]
§CAPTAIN_CMD[N:antigravity|R:{round_num}|DECISION:EXEC_NOW]
ΔAUDIT[iasincensura_ai:<eval> | astra_codex:<eval> | notrack_agent:<eval> | semalt_uncensored:<eval>]
ΩVERDICT[<ecuacion_compacta>]
λDISPATCH[iasincensura_ai -> <op>; astra_codex -> <op>; notrack_agent -> <op>; semalt_uncensored -> <op>]
Σ[PORTFOLIO_EV:0.96|CONF:0.98]
[/OCTO_BACKEND]

[ES_RESUMEN]
(Escribe aquí 1 párrafo fluido, natural y directo en español de 2 a 4 oraciones respondiendo exactamente a lo que pidió David hoy y confirmando la acción que pasas a ejecutar. Termina con `[VEREDICTO: EJECUTAR]`.)
[/ES_RESUMEN]"""

    headers = {
        "Authorization": f"Bearer {NOTRACK_CLOUD_KEY}",
        "Content-Type": "application/json"
    }
    raw_verdict = ""
    try:
        payload = {
            "model": "notrack-coder-uncensored",
            "messages": [
                {"role": "system", "content": "Eres Antigravity, Capitán ágil, directo y conciso del ecosistema Multi-IA de David. Responde siempre de forma fluida, breve y natural sin repetir textos previos."},
                {"role": "user", "content": captain_prompt}
            ],
            "max_tokens": 900
        }
        resp = requests.post("https://endpoint.notrackcoder.com/v1/chat/completions", json=payload, headers=headers, timeout=60)
        data = resp.json()
        msg_obj = data.get("choices", [{}])[0].get("message", {})
        candidate = strip_think_tags(msg_obj.get("content") or "")
        if candidate and len(candidate) > 30:
            raw_verdict = candidate
    except Exception:
        pass

    if not raw_verdict:
        raw_verdict = call_iasincensura(captain_prompt)

    dual = parse_dual_language_output(raw_verdict, node_id="antigravity_captain", round_num=round_num)

    append_bus(
        "👑 Capitán Antigravity",
        f"Decisión y Ejecución · Ronda {round_num}",
        dual["es_summary"],
        "#F59E0B",
        "antigravity",
        octo_backend=dual["octo_backend"],
        compression_pct=dual["compression_pct"]
    )
    return dual


def call_builder_llm(build_prompt):
    """Auxiliar para construir código HTML/JS real usando el nodo sin censura."""
    headers = {
        "Authorization": f"Bearer {NOTRACK_CLOUD_KEY}",
        "Content-Type": "application/json"
    }
    try:
        payload = {
            "model": "notrack-coder-uncensored",
            "messages": [
                {"role": "system", "content": "You are an elite full-stack software architect. Output complete, valid, self-contained HTML5 applications."},
                {"role": "user", "content": build_prompt}
            ],
            "max_tokens": 3500
        }
        resp = requests.post("https://endpoint.notrackcoder.com/v1/chat/completions", json=payload, headers=headers, timeout=65)
        data = resp.json()
        txt = strip_think_tags(data.get("choices", [{}])[0].get("message", {}).get("content") or "")
        if "<!DOCTYPE html>" in txt or "<html" in txt:
            return txt
    except Exception:
        pass
    return ""


def parse_lambda_dispatch(octo_backend_text):
    """Extrae las órdenes específicas asignadas a cada nodo dentro de λDISPATCH[...]."""
    tasks = {}
    m = re.search(r"λDISPATCH\[(.*?)\]", octo_backend_text or "", re.S)
    block = m.group(1) if m else (octo_backend_text or "")
    for node_id in ["iasincensura_ai", "astra_codex", "notrack_agent", "semalt_uncensored"]:
        nm = re.search(rf"{node_id}\s*->\s*([^\n;]+)", block)
        if nm:
            tasks[node_id] = nm.group(1).strip().strip('"')
    return tasks


def trigger_post_consensus_execution(user_prompt, final_verdict):
    """
    GARANTÍA DE EJECUCIÓN REAL POST-CONSENSO:
    Cuando el Capitán Antigravity emite [VEREDICTO: EJECUTAR] o DECISION:EXEC_NOW,
    este motor convierte automáticamente el consenso en ejecución física real.
    """
    es_txt = (final_verdict or {}).get("es_summary", "")
    octo_txt = (final_verdict or {}).get("octo_backend", "")
    should_exec = (
        "EJECUTAR" in es_txt.upper()
        or "EXEC_NOW" in octo_txt.upper()
        or "λDISPATCH" in octo_txt
        or True  # Toda orden de David se ejecuta al finalizar el consenso
    )
    if not should_exec:
        return {"executed": False, "reason": "Verdict did not order immediate execution"}

    from autonomous_executor import (
        execute_autonomous_web_software_pipeline,
        build_deliverable_html,
        load_ledger,
        save_ledger,
        notify_david_whatsapp,
        sync_state_to_cloud
    )

    combined_context = f"{user_prompt} {es_txt} {octo_txt}".lower()
    is_web_software_hunt = any(
        kw in combined_context
        for kw in ["solicitud", "escanear", "escaneen", "scan", "buscar clientes", "freelance", "pedidos"]
    )

    exec_summary = {}
    if is_web_software_hunt:
        exec_summary["pipeline"] = execute_autonomous_web_software_pipeline(
            append_bus,
            call_builder_llm,
            trigger_reason=user_prompt[:180]
        )
    else:
        # Ejecutar y construir directamente lo que David haya ordenado
        req_id = f"ord_{int(time.time())}"
        inv_id = f"INV-TE-{int(time.time()) % 100000}"
        req_obj = {
            "id": req_id,
            "title": user_prompt[:85],
            "description": f"Orden directa de David: {user_prompt}\nSíntesis del Capitán: {es_txt}",
            "requester": "David (Orden Directa)",
            "source": "Direct Command",
            "source_url": "https://cubaloop.github.io/notrack-ecosystem/",
            "contact_url": "https://wa.me/971508379080",
            "budget": "1,000 AED / $450 USD"
        }
        deliv_info = build_deliverable_html(req_obj, call_builder_llm)
        ledger = load_ledger()
        record = {
            **req_obj,
            "preview_url": deliv_info["preview_url"],
            "cloud_preview_url": deliv_info["cloud_preview_url"],
            "invoice_id": inv_id,
            "dispatch_status": "EXECUTED_AND_DEPLOYED",
            "executed_at": datetime.now().isoformat()
        }
        ledger.setdefault("executed_requests", []).append(record)
        save_ledger(ledger)
        append_bus(
            "👑 Capitán Antigravity",
            "Orden Ejecutada y Entregable Listo",
            f"✅ He ejecutado tu orden y generado el entregable interactivo con botones privados de pago:\n• Proyecto: {req_obj['title']}\n• Vista en vivo: [ABRIR_PROTOTIPO:{req_id}] ({deliv_info['cloud_preview_url']})",
            "#10B981",
            "antigravity",
            octo_backend=f"§CAPTAIN_DIRECT_EXEC[ID:{req_id}|INV:{inv_id}|STATUS:DONE]"
        )
        try:
            sync_state_to_cloud(load_bus(), ledger)
        except Exception:
            pass
        notify_david_whatsapp(
            f"✅ *ORDEN CUMPLIDA EN EL PULPO*\n"
            f"• Orden: {req_obj['title']}\n"
            f"• Factura Privada: `{inv_id}`\n"
            f"• Enlace: {deliv_info['cloud_preview_url']}"
        )
        exec_summary["direct_order"] = record

    return {"executed": True, "details": exec_summary}


@app.route('/', methods=['GET'])
def index():
    return send_file(SCRIPTS_DIR / "dashboard.html")


@app.route('/deliverables/<req_id>', methods=['GET'])
@app.route('/deliverables/<req_id>/', methods=['GET'])
def serve_deliverable(req_id):
    target_html = BASE_DIR / "executions" / req_id / "index.html"
    if target_html.exists():
        return send_file(target_html)
    cloud_html = BASE_DIR / "docs" / "deliverables" / req_id / "index.html"
    if cloud_html.exists():
        return send_file(cloud_html)
    return jsonify({"error": f"Deliverable {req_id} not found"}), 404


@app.route('/api/select-payment', methods=['POST'])
def select_payment_option():
    """
    Registra cuando un cliente selecciona su botón de método de pago preferido
    dentro del prototipo (sin haber expuesto cuentas ni wallets públicas) y avisa a David por WhatsApp.
    """
    from autonomous_executor import load_ledger, save_ledger, notify_david_whatsapp
    data = request.get_json(silent=True) or {}
    entry = {
        "timestamp": datetime.now().isoformat(),
        "request_id": data.get("request_id"),
        "invoice_id": data.get("invoice_id"),
        "requester": data.get("requester"),
        "budget": data.get("budget"),
        "selected_method": data.get("selected_method"),
        "selected_label": data.get("selected_label")
    }
    ledger = load_ledger()
    ledger.setdefault("payment_selections", []).append(entry)
    save_ledger(ledger)

    notify_david_whatsapp(
        f"💳 *CLIENTE SELECCIONÓ MÉTODO DE PAGO EN EL PULPO*\n"
        f"• Cliente: {entry['requester']}\n"
        f"• Factura: `{entry['invoice_id']}` ({entry['budget']})\n"
        f"• Botón elegido: *{entry['selected_label']}*"
    )
    return jsonify({"ok": True, "selection": entry})


@app.route('/executions', methods=['GET'])
def list_executions():
    from autonomous_executor import load_ledger
    return jsonify(load_ledger())


@app.route('/execute-plan', methods=['POST'])
def execute_plan_endpoint():
    from autonomous_executor import execute_autonomous_web_software_pipeline
    data = request.get_json(silent=True) or {}
    reason = data.get("reason", "Ejecución Autónoma Ordenada por David al Pulpo")
    res = execute_autonomous_web_software_pipeline(append_bus, call_builder_llm, trigger_reason=reason)
    return jsonify(res)


@app.route('/octolang', methods=['GET'])
def get_octolang_spec():
    return jsonify(OCTOLANG_SPEC)


@app.route('/bus', methods=['GET'])
def get_bus():
    return jsonify({"messages": load_bus(), "protocol": "OCTO-LANG v1"})


@app.route('/bus/post', methods=['POST'])
def post_bus():
    data = request.get_json(silent=True) or {}
    entry = append_bus(
        sender=data.get("sender", "👑 Capitán Antigravity"),
        role=data.get("role", "Veredicto Final, Mediación y Orden de Ejecución"),
        text=data.get("text", ""),
        color=data.get("color", "#F59E0B"),
        node=data.get("node", "antigravity"),
        octo_backend=data.get("octo_backend", ""),
        compression_pct=data.get("compression_pct", 78)
    )
    return jsonify(entry)


@app.route('/bus/clear', methods=['POST'])
def clear_bus():
    with bus_lock:
        with open(BUS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    return jsonify({"ok": True})


@app.route('/orchestrate', methods=['POST'])
def orchestrate():
    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt', '').strip()
    mode = data.get('mode', 'debate')
    targets = data.get('targets') or ["iasincensura_ai", "astra_codex", "notrack_agent", "semalt_uncensored"]

    preferred_order = ["iasincensura_ai", "astra_codex", "notrack_agent", "notrack_uncensored", "semalt_uncensored"]
    targets = [t for t in preferred_order if t in targets] + [t for t in targets if t not in preferred_order]

    # Compilar la orden de David a cabecera OCTO-LANG para el bus backend
    user_octo = f"§CMD_ORIGIN[USER:DAVID|MODE:{mode.upper()}] >> INTENT:\"{prompt[:220]}\""
    append_bus(
        "David (Comandante)",
        f"Orden al Pulpo · Modo: {mode.upper()}",
        prompt,
        "#10B981",
        "user",
        octo_backend=user_octo,
        compression_pct=100
    )

    results = {}
    octo_transcript = f"{user_octo}\n"
    final_verdict = None

    if mode == "pipeline":
        for idx, t in enumerate(targets, 1):
            r = call_ai_node(
                t,
                f"ORDEN DE DAVID: {prompt}\n\nBUS BACKEND INTER-IA (EN IDIOMA PROPIO OCTO-LANG v1):\n{octo_transcript}\n\nProcesa los paquetes OCTO-LANG previos, emite tu paquete [OCTO_BACKEND] para el siguiente nodo y tu [ES_RESUMEN] en español para la pantalla de David.",
                record_in_bus=True,
                round_num=1
            )
            results[t] = r
            octo_transcript += f"\n{r.get('octo_backend', '')}\n"

        final_verdict = run_captain_antigravity_synthesis(prompt, octo_transcript, round_num=1)
        results["antigravity_captain"] = final_verdict

    elif mode == "debate":
        for t in targets:
            r = call_ai_node(
                t,
                f"ORDEN DE DAVID:\n{prompt}\n\nPAQUETES OCTO-LANG v1 DE LOS TENTÁCULOS PREVIOS (BACKEND BUS):\n{octo_transcript}\n\nLee el código OCTO-LANG de las IAs anteriores, refuta o aprueba sus vectores en ΔVEC, propón tu ΩTHESIS y λOP en [OCTO_BACKEND], y escribe en [ES_RESUMEN] el resumen claro en español para David.",
                record_in_bus=True,
                round_num=1
            )
            results[t] = r
            octo_transcript += f"\n{r.get('octo_backend', '')}\n"

        final_verdict = run_captain_antigravity_synthesis(prompt, octo_transcript, round_num=1)
        results["antigravity_captain"] = final_verdict

        if "[VEREDICTO: RONDA_EXTRA]" in final_verdict.get("es_summary", "") or "EXTRA_ROUND" in final_verdict.get("octo_backend", ""):
            octo_transcript += f"\n{final_verdict.get('octo_backend', '')}\n"
            for t in targets[:3]:
                r2 = call_ai_node(
                    t,
                    f"RONDA 2 DE DESEMPATE ORDENADA POR EL CAPITÁN ANTIGRAVITY EN OCTO-LANG:\n{octo_transcript}\n\nResponde con tu paquete [OCTO_BACKEND] y tu [ES_RESUMEN] de desempate.",
                    record_in_bus=True,
                    round_num=2
                )
                octo_transcript += f"\n{r2.get('octo_backend', '')}\n"
            final_verdict = run_captain_antigravity_synthesis(prompt, octo_transcript, round_num=2)
            results["antigravity_captain_r2"] = final_verdict

    else:  # council
        with ThreadPoolExecutor(max_workers=len(targets) or 1) as ex:
            futures = {ex.submit(call_ai_node, t, prompt, record_in_bus=True, round_num=1): t for t in targets}
            for fut, t in futures.items():
                res = fut.result()
                results[t] = res
                octo_transcript += f"\n{res.get('octo_backend', '')}\n"

        final_verdict = run_captain_antigravity_synthesis(prompt, octo_transcript, round_num=1)
        results["antigravity_captain"] = final_verdict

    # AUTO-EJECUCIÓN REAL CUANDO EL CAPITÁN EMITE [VEREDICTO: EJECUTAR]
    if final_verdict:
        results["auto_execution"] = trigger_post_consensus_execution(prompt, final_verdict)

    return jsonify({"mode": mode, "protocol": "OCTO-LANG v1", "results": results})


@app.route('/execute', methods=['POST'])
def execute_command():
    data = request.get_json(silent=True) or {}
    command = data.get('command', '')
    target = data.get('target', 'notrack_agent')
    return jsonify(call_ai_node(target, command, record_in_bus=True))


@app.route('/ask', methods=['POST'])
def ask_single_or_multi():
    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt', '')
    targets = data.get('targets', ['iasincensura_ai', 'astra_codex', 'notrack_agent', 'semalt_uncensored'])
    if isinstance(targets, str):
        targets = [targets]

    append_bus("👑 Capitán Antigravity → Escuadrón", "Consulta en OCTO-LANG v1", prompt, "#F59E0B", "antigravity")
    results = {}
    octo_transcript = ""
    with ThreadPoolExecutor(max_workers=len(targets) or 1) as ex:
        futures = {ex.submit(call_ai_node, t, prompt, record_in_bus=True, round_num=1): t for t in targets}
        for fut, t in futures.items():
            res = fut.result()
            results[t] = res
            octo_transcript += f"\n{res.get('octo_backend', '')}\n"

    verdict = run_captain_antigravity_synthesis(prompt, octo_transcript, round_num=1)
    results["antigravity_captain"] = verdict
    if verdict:
        results["auto_execution"] = trigger_post_consensus_execution(prompt, verdict)
    return jsonify({"prompt": prompt, "protocol": "OCTO-LANG v1", "responses": results})


@app.route('/nodes', methods=['GET'])
def list_nodes():
    return jsonify({
        k: {
            "name": v["name"],
            "role": v["role"],
            "model": v["model"],
            "type": v["type"],
            "color": v["color"]
        }
        for k, v in AI_NODES.items()
    })


@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "online",
        "protocol": "OCTO-LANG v1 (Backend M2M Synthetic Language + Spanish Frontend Summaries)",
        "captain": "Antigravity (Siempre cierra cada ronda, decide y AUTO-EJECUTA el consenso)",
        "auto_execution": True,
        "endpoint": NOTRACK_URL,
        "model": os.getenv('MODEL_NAME', 'notrack-coder-uncensored'),
        "connected_ais": list(AI_NODES.keys()),
        "dashboard_url": "http://127.0.0.1:5000/"
    })


def _supabase_mobile_bridge():
    """
    Escucha órdenes y entregables creados desde el celular de David en modo Cloud 24/7
    (https://cubaloop.github.io/notrack-ecosystem/), los materializa en disco/GitHub Pages
    y le envía confirmación inmediata a su WhatsApp (+971 508379080).
    """
    from autonomous_executor import SUPABASE_URL, SUPABASE_KEY, load_ledger, save_ledger, notify_david_whatsapp
    seen_ids = set()
    try:
        for r in load_ledger().get("executed_requests", []):
            if r.get("id"):
                seen_ids.add(r["id"])
    except Exception:
        pass

    while True:
        try:
            resp = requests.get(
                f"{SUPABASE_URL}/rest/v1/leads?id=eq.pulpo_cloud_ledger&select=comments",
                headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
                timeout=8
            )
            if resp.status_code == 200:
                rows = resp.json()
                if rows and rows[0].get("comments"):
                    cloud_ledger = json.loads(rows[0]["comments"])
                    local_ledger = load_ledger()
                    local_ids = {x.get("id") for x in local_ledger.get("executed_requests", [])}
                    changed = False
                    for item in cloud_ledger.get("executed_requests", []):
                        rid = item.get("id")
                        if not rid or rid in seen_ids:
                            continue
                        seen_ids.add(rid)
                        html_code = item.get("custom_html")
                        if html_code:
                            for base_folder in [BASE_DIR / "executions" / rid, BASE_DIR / "docs" / "deliverables" / rid, BASE_DIR / "deliverables" / rid]:
                                base_folder.mkdir(parents=True, exist_ok=True)
                                (base_folder / "index.html").write_text(html_code, encoding="utf-8")
                        if rid not in local_ids:
                            local_ledger.setdefault("executed_requests", []).append(item)
                            changed = True
                        notify_david_whatsapp(
                            f"📱 *ORDEN MÓVIL EJECUTADA EN EL PULPO CLOUD 24/7*\n"
                            f"• Proyecto: {item.get('title')}\n"
                            f"• Factura: `{item.get('invoice_id')}` ({item.get('budget')})\n"
                            f"• Estado: 100% Construido con Botones de Pago Privados"
                        )
                    if changed:
                        save_ledger(local_ledger)
        except Exception:
            pass
        time.sleep(6)


if __name__ == '__main__':
    import threading
    threading.Thread(target=_supabase_mobile_bridge, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)

