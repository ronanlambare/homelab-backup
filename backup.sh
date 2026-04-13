#!/bin/bash
SOURCE="/hdd-01/photo/immich"
DEST="aubin-srv:/data/backups/immich/"
LOG_FILE="/var/log/backup/rclone.log"

export TZ="Europe/Paris"

send_telegram() {
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=$1"
}

MOMENT=$(date '+%H:%M le %d/%m/%Y')
send_telegram "🔄 Backup démarré à ${MOMENT}"

# On vide le log rclone
> "${LOG_FILE}"

rclone sync "${SOURCE}" "${DEST}" \
  --log-file "${LOG_FILE}" \
  --log-level INFO
STATUS=$?

FIN=$(date '+%H:%M le %d/%m/%Y')

if [ $STATUS -eq 0 ]; then
  # 1. On extrait les stats du transfert actuel
  STATS=$(tail -n 20 "${LOG_FILE}" | grep -E "Transferred:|Checks:|Elapsed time:" | sed 's/^[[:space:]]*//')

  # 2. On récupère la taille TOTALE du dossier sur le serveur distant
  # --json permet de récupérer les données proprement avec rclone size
  TOTAL_SIZE=$(rclone size "${DEST}" --human-readable | grep "Total size" | cut -d: -f2 | sed 's/^[[:space:]]*//')

  MESSAGE="✅ Backup terminé à ${FIN}
  
📊 Rapport du transfert :
${STATS}

storage_rounded Stockage total distant :
📦 ${TOTAL_SIZE}"

  send_telegram "${MESSAGE}"
else
  send_telegram "❌ Backup ÉCHOUÉ à ${FIN} (Code: ${STATUS})"
fi