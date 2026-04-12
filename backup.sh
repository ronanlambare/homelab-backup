#!/bin/bash
SOURCE="/hdd-01/photo/immich"
DEST="aubin-srv:/data/backups/immich/"

send_telegram() {
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
    -d chat_id="${TELEGRAM_CHAT_ID}" \
    -d text="$1"
}

START=$(date '+%Y-%m-%d %H:%M:%S')
send_telegram "🔄 Backup démarré à ${START}"

> "${LOG_FILE}"  # vide le log avant chaque run

rclone sync "${SOURCE}" "${DEST}" \
  --log-file "/tmp/rclone.log" \
  --log-level INFO
STATUS=$?

END=$(date '+%Y-%m-%d %H:%M:%S')
FILES=$(grep -c '^>' /tmp/rclone.log || echo 0)

if [ $STATUS -eq 0 ]; then
  send_telegram "✅ Backup terminé à ${END} — ${FILES} fichier(s) transféré(s)"
else
  send_telegram "❌ Backup ÉCHOUÉ à ${END} — Code erreur: ${STATUS}"
fi