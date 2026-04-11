#!/bin/bash
SOURCE="/hdd-01/ton-dossier/"
DEST="bkp_ronan@192.168.1.210:/backups/"

# TOKEN et CHAT_ID injectés via variables d'environment
send_telegram() {
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
    -d chat_id="${TELEGRAM_CHAT_ID}" \
    -d text="$1"
}

START=$(date '+%Y-%m-%d %H:%M:%S')
send_telegram "🔄 Backup démarré à ${START}"

rsync -avz --update -e "ssh -i /root/.ssh/id_ed25519 -o StrictHostKeyChecking=no" \
  "${SOURCE}" "${DEST}" > /tmp/rsync.log 2>&1
STATUS=$?

END=$(date '+%Y-%m-%d %H:%M:%S')
FILES=$(grep -c '^>' /tmp/rsync.log || echo 0)

if [ $STATUS -eq 0 ]; then
  send_telegram "✅ Backup terminé à ${END} — ${FILES} fichier(s) transféré(s)"
else
  send_telegram "❌ Backup ÉCHOUÉ à ${END} — Code erreur: ${STATUS}"
fi