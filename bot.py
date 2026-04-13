import os
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Récupération des variables d'environnement
TOKEN = os.getenv('TELEGRAM_TOKEN')
AUTHORIZED_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
DEST = "aubin-srv:/data/backups/immich/"

async def is_authorized(update: Update):
    """Vérifie si l'utilisateur est celui configuré dans le Docker Compose."""
    current_chat_id = str(update.message.chat_id)
    if current_chat_id == AUTHORIZED_CHAT_ID:
        return True
    else:
        print(f"⚠️ Accès refusé pour le Chat ID : {current_chat_id}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update): return
    await update.message.reply_text("👋 Bot de backup sécurisé opérationnel ! Tape /help.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update): return
    text = (
        "🤖 *Commandes autorisées :*\n\n"
        "/size - Voir la taille totale du backup distant\n"
        "/status - Voir le dernier log de transfert\n"
        "/help - Afficher ce menu"
    )
    await update.message.reply_markdown(text)

async def get_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update): return
    
    await update.message.reply_text("🔍 Interrogation du serveur distant...")
    
    try:
        # rclone size sur le dossier de destination
        cmd = ["rclone", "size", DEST, "--human-readable"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        
        if result.returncode == 0:
            # On formate un peu le retour pour que ce soit joli
            output = result.stdout.replace("Total objects:", "Fichiers :").replace("Total size:", "Taille totale :")
            await update.message.reply_text(f"📦 *État du stockage distant :*\n{output}", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Erreur rclone : {result.stderr}")
    except Exception as e:
        await update.message.reply_text(f"💥 Erreur système : {str(e)}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update): return
    
    log_path = "/var/log/backup/rclone.log"
    if os.path.exists(log_path):
        # On récupère les 15 dernières lignes pour avoir le dernier bloc de stats
        with open(log_path, 'r') as f:
            lines = f.readlines()
            last_lines = "".join(lines[-15:])
        await update.message.reply_text(f"📋 *Dernières lignes du log :*\n```\n{last_lines}\n```", parse_mode='Markdown')
    else:
        await update.message.reply_text("⚠️ Aucun fichier de log trouvé.")

if __name__ == '__main__':
    if not TOKEN or not AUTHORIZED_CHAT_ID:
        print("❌ Erreur : TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID non configuré.")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("size", get_size))
    app.add_handler(CommandHandler("status", status_command))
    
    print("🚀 Bot sécurisé en ligne...")
    app.run_polling()