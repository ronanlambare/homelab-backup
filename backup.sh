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
  # LOGIQUE POUR ISOLER LE DERNIER BLOC :
  # 1. tac : lit à l'envers
  # 2. sed : s'arrête dès qu'il voit la ligne de log INFO vide qui marque le début du bloc
  # 3. tac : remet à l'endroit
  # 4. grep : filtre les lignes utiles (on ajoute Deleted car tu en as eu un)
  STATS=$(tac "${LOG_FILE}" | sed -n '1,/INFO  : $/p' | tac | grep -E "Transferred:|Checks:|Deleted:|Elapsed time:" | sed 's/^[[:space:]]*//')
  
  MESSAGE="✅ Backup terminé à ${FIN}
  
📊 Rapport du transfert :
${STATS}"

  send_telegram "${MESSAGE}"
else
  send_telegram "❌ Backup ÉCHOUÉ à ${FIN} (Code: ${STATUS})"
fi