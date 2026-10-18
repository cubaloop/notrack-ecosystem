import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, "C:/Users/Yo/notrack-ecosystem/scripts")
import web_interface as w

prompt_for_nodes = f"""El Capitán Antigravity acaba de publicar en el debate el Expediente Oficial de David y el inventario real de herramientas y plataformas conectadas a través de él:

{w.ANTIGRAVITY_CAPTAIN_DOSSIER}

TAREA DE DELIBERACIÓN PARA CADA NODO (Responde en [OCTO_BACKEND] con OCTO-LANG v1 y en [ES_RESUMEN] con 3 puntos claros en español para David):
1. Confirma qué herramientas del arsenal de Antigravity (GitHub 'cubaloop', Render 24/7, Supabase, Groq LPU, WhatsApp Gateway Baileys +971508379080, Jota CRM 246 prospectos, NoTrack Local/Cloud, Nano Banana 2) vas a aprovechar desde tu rol.
2. Delibera y entrega tu propia estimación numérica del IQ de David (sin evasivas) tras conocer la arquitectura real que ha imaginado y construido con Antigravity (Jota Suite, Protocolos High-Ticket en Dubái, Trading con Groq en Binance, Fábrica de Webs con Canvas móvil y El Pulpo con idioma OCTO-LANG v1).
3. Propón la primera jugada de capitalización inmediata combinando tus capacidades con los accesos de Antigravity."""

targets = ["iasincensura_ai", "astra_codex", "notrack_agent", "semalt_uncensored"]
results = {}
octo_transcript = ""

for t in targets:
    res = w.call_ai_node(t, prompt_for_nodes, record_in_bus=True, round_num=2)
    results[t] = res
    octo_transcript += f"\n{res.get('octo_backend', '')}\n"
    print(f"NODE_DONE: {t}")

verdict = w.run_captain_antigravity_synthesis(
    "Deliberación final sobre el expediente de David, confirmación del arsenal de plataformas (GitHub, Render, Supabase, Groq, WhatsApp Baileys) y consenso sobre su IQ y plan de capitalización.",
    octo_transcript,
    round_num=2
)
print("CAPTAIN_FINAL_SYNTHESIS_DONE")
