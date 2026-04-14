#!/bin/bash
# --- Configuration ---
SOURCE="/hdd-01/photo/immich"
DEST="aubin-srv:/data/backups/immich/"
LOG_FILE="/var/log/backup/rclone.log"
REMOTE_HOST="aubin-srv"

export TZ="Europe/Paris"

# Fonction d'envoi Telegram
send_telegram() {
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=$1"
}

# --- 1. Vérification de la présence du serveur distant ---
# On utilise nc (netcat) pour vérifier le port 22 avec un timeout de 5s
if ! nc -z -w 5 ${REMOTE_HOST} 22; then
  MOMENT=$(date '+%H:%M le %d/%m/%Y')
  send_telegram "⚠️ ALERTE : Le serveur de backup (${REMOTE_HOST}) est INJOIGNABLE à ${MOMENT}. Le backup a été annulé."
  exit 1
fi

# --- 2. Lancement du Backup ---
MOMENT=$(date '+%H:%M le %d/%m/%Y')
send_telegram "🔄 Backup démarré à ${MOMENT}"

# On vide le log rclone précédent
> "${LOG_FILE}"

rclone sync "${SOURCE}" "${DEST}" \
  --log-file "${LOG_FILE}" \
  --log-level INFO
STATUS=$?

FIN=$(date '+%H:%M le %d/%m/%Y')

# --- 3. Analyse du résultat et Rapport ---
if [ $STATUS -eq 0 ]; then
  # Extraction des statistiques du log rclone
  STATS=$(tac "${LOG_FILE}" | sed -n '1,/INFO  : $/p' | tac | grep -E "Transferred:|Checks:|Deleted:|Elapsed time:" | sed 's/^[[:space:]]*//')
  
  MESSAGE="✅ Backup terminé avec succès à ${FIN}
  
📊 Rapport rclone :
${STATS:-Pas de modifications détectées.}"

  send_telegram "${MESSAGE}"
else
  # En cas d'erreur, on envoie les 5 dernières lignes du log pour débugger
  ERROR_LOG=$(tail -n 5 "${LOG_FILE}")
  send_telegram "❌ Backup ÉCHOUÉ à ${FIN} (Code: ${STATUS})
  
Détails :
${ERROR_LOG}"
fi