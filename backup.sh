#!/bin/bash
SOURCE="/hdd-01/photo/immich"
DEST="backup-sftp:/backups/immich/"
LOG_FILE="/tmp/rclone.log"

send_telegram() {
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
    -d chat_id="${TELEGRAM_CHAT_ID}" \
    -d text="$1"
}

START=$(date '+%Y-%m-%d %H:%M:%S')
send_telegram "🔄 Backup démarré à ${START}"

> "${LOG_FILE}"  # vide le log avant chaque run

rclone copy "${SOURCE}" "${DEST}" \
  --update \
  --log-file "${LOG_FILE}" \
  --log-level INFO
STATUS=$?

END=$(date '+%Y-%m-%d %H:%M:%S')
FILES=$(grep -c 'Copied' "${LOG_FILE}" || echo 0)
ERRORS=$(grep -c 'ERROR' "${LOG_FILE}" || echo 0)

if [ $STATUS -ne 0 ] || [ "$ERRORS" -gt 0 ]; then
  FIRST_ERROR=$(grep 'ERROR' "${LOG_FILE}" | head -3)
  send_telegram "❌ Backup ÉCHOUÉ à ${END} — ${ERRORS} erreur(s), ${FILES} fichier(s) transféré(s)
${FIRST_ERROR}"
else
  send_telegram "✅ Backup terminé à ${END} — ${FILES} fichier(s) transféré(s)"
fi