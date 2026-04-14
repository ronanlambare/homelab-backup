import os
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Récupération des variables d'environnement
TOKEN = os.getenv('TELEGRAM_TOKEN')
AUTHORIZED_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
DEST = "aubin-srv:/data/backups/immich/"
REMOTE_HOST = "aubin-srv"

async def is_authorized(update: Update):
    """Vérifie si l'utilisateur est autorisé."""
    current_chat_id = str(update.message.chat_id)
    if current_chat_id == AUTHORIZED_CHAT_ID:
        return True
    print(f"⚠️ Accès refusé pour le Chat ID : {current_chat_id}")
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update): return
    await update.message.reply_text("👋 Bot de backup opérationnel !\nTape /help pour voir les commandes.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update): return
    text = (
        "🤖 *Commandes disponibles :*\n\n"
        "/ping - Vérifier la connexion avec le serveur distant\n"
        "/size - Voir la taille totale sur le serveur\n"
        "/status - Voir le dernier log de transfert\n"
        "/help - Afficher ce menu"
    )
    await update.message.reply_markdown(text)

async def ping_remote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Vérifie si le serveur de backup répond sur le réseau."""
    if not await is_authorized(update): return
    await update.message.reply_text(f"📡 Test de connexion vers {REMOTE_HOST}...")
    
    # Utilisation de netcat pour vérifier le port 22
    check = subprocess.run(["nc", "-z", "-w", "5", REMOTE_HOST, "22"])
    
    if check.returncode == 0:
        await update.message.reply_text(f"✅ {REMOTE_HOST} est EN LIGNE.")
    else:
        await update.message.reply_text(f"❌ {REMOTE_HOST} est INJOIGNABLE (Port 22 fermé ou timeout).")

async def get_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update): return
    await update.message.reply_text("🔍 Calcul de la taille distante...")
    try:
        cmd = ["rclone", "size", DEST, "--human-readable"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            output = result.stdout.replace("Total objects:", "Fichiers :").replace("Total size:", "Taille totale :")
            await update.message.reply_text(f"📦 *État du stockage :*\n{output}", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Erreur rclone : {result.stderr}")
    except Exception as e:
        await update.message.reply_text(f"💥 Erreur : {str(e)}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update): return
    log_path = "/var/log/backup/rclone.log"
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            lines = f.readlines()
            last_lines = "".join(lines[-15:])
        await update.message.reply_text(f"📋 *Dernières lignes du log :*\n```\n{last_lines}\n```", parse_mode='Markdown')
    else:
        await update.message.reply_text("⚠️ Aucun fichier de log trouvé.")

if __name__ == '__main__':
    if not TOKEN or not AUTHORIZED_CHAT_ID:
        print("❌ Erreur : TOKEN ou CHAT_ID non configuré.")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping_remote))
    app.add_handler(CommandHandler("size", get_size))
    app.add_handler(CommandHandler("status", status_command))
    
    print("🚀 Bot en ligne...")
    app.run_polling()