#!/bin/bash

# --- CONFIGURAZIONE ---
PROJECT_DIR="/disco2/dati_home/Scaricati/Personale/esempi/appuntidiprogrammazione"
LOG_FILE="$PROJECT_DIR/esecuzione.log"

# Funzione per stampare con data e ora precisa
log_echo() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_echo "------------------------------------------------"
log_echo "🚀 AVVIO ROUTINE GENERAZIONE NOTIZIE"
log_echo "------------------------------------------------"

# 1. Spostamento nella cartella del progetto
cd "$PROJECT_DIR" || { log_echo "❌ ERRORE: Cartella non trovata!"; exit 1; }

# 2. Controllo se Ollama è attivo
if ! pgrep -x "ollama" > /dev/null
then
    log_echo "⚠️ Ollama non è attivo. Tento l'avvio..."
    ollama serve &
    sleep 5
fi

# 3. Controllo modelli
log_echo "🧠 Verifica modelli Ollama..."
MODELS=$(ollama list)
if [[ ! $MODELS == *"mistral"* ]] || [[ ! $MODELS == *"qwen2.5-coder"* ]]; then
    log_echo "❌ ERRORE: Modelli mancanti."
    exit 1
fi

# 4. Avvio Script Python
log_echo "🐍 Avvio script Python (Output in tempo reale)..."

# SPIEGAZIONE DELLE MODIFICHE:
# - PYTHONUNBUFFERED=1: Obbliga Python a sputare fuori i print immediatamente.
# - stdbuf -oL: Forza il sistema operativo a non bufferizzare le righe.
# - 2>&1 | tee: Unisce errori e output standard e li scrive sia su file che a video.

export QT_QPA_PLATFORM=xcb
export PYTHONUNBUFFERED=1

stdbuf -oL pipenv run python genera_notizie.py 2>&1 | tee "$LOG_FILE"

# 5. Esito finale
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    log_echo "------------------------------------------------"
    log_echo "✅ OPERAZIONE COMPLETATA CON SUCCESSO!"
else
    log_echo "------------------------------------------------"
    log_echo "❌ QUALCOSA È ANDATO STORTO. Controlla $LOG_FILE"
fi