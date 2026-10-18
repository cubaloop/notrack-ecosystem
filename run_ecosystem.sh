#!/bin/bash
cd ~/notrack-ecosystem

echo "🚀 Inicializando Ecosistema NoTrack..."

# Exportar variables
export $(grep -v '^#' .env | xargs)

# Iniciar el orquestador en segundo plano
nohup python scripts/orchestrator.py > logs/orchestrator.log 2>&1 &
ORCH_PID=$!
echo "[System] Orchestrator PID: $ORCH_PID"

# Iniciar la interfaz web en segundo plano
nohup python scripts/web_interface.py > logs/web.log 2>&1 &
WEB_PID=$!
echo "[System] Web Interface PID: $WEB_PID"

echo "✅ Ecosistema activo."
echo "   - Orchestrator corriendo."
echo "   - Web Interface disponible en http://127.0.0.1:5000"
echo "   - Logs en logs/"

# Mantener el script vivo para capturar señales de parada
wait
