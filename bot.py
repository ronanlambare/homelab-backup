import os
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- CONFIGURATION ET SÉCURITÉ ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
AUTHORIZED_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
REMOTE_HOST = "aubin-srv"

async def is_authorized(update: Update) -> bool:
    """Vérification de l'ID utilisateur Telegram."""
    if not update.message:
        return False
    current_chat_id = str(update.message.chat_id)
    if current_chat_id == AUTHORIZED_CHAT_ID:
        return True
    
    print(f"⚠️ Accès refusé pour l'ID : {current_chat_id}")
    await update.message.reply_text("🚫 Accès non autorisé.")
    return False

# --- COMMANDES ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update): return
    await update.message.reply_text("👋 Bot de backup opérationnel et sécurisé !")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update): return
    text = (
        "🤖 *Commandes disponibles :*\n\n"
        "/ping : Vérifier la connexion vers le serveur\n"
        "/backup : Lancer manuellement le script de backup\n"
        "/status : Voir le rapport du dernier transfert\n"
        "/help : Afficher ce menu"
    )
    await update.message.reply_markdown(text)

async def ping_remote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Vérifie si le port SSH est ouvert (Preuve que le tunnel et le serveur sont UP)."""
    if not await is_authorized(update): return
    await update.message.reply_text(f"📡 Test de connexion vers {REMOTE_HOST}...")
    
    # Utilisation de netcat (nc)
    check = subprocess.run(["nc", "-z", "-w", "5", REMOTE_HOST, "22"])
    
    if check.returncode == 0:
        await update.message.reply_text(f"✅ {REMOTE_HOST} répond présent.")
    else:
        await update.message.reply_text(f"❌ {REMOTE_HOST} est injoignable.")

async def run_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exécute le script backup.sh en arrière-plan."""
    if not await is_authorized(update): return
    await update.message.reply_text("🚀 Lancement du backup forcé...")
    try:
        # Lancement asynchrone pour ne pas bloquer le bot
        subprocess.Popen(["/bin/bash", "/backup.sh"])
    except Exception as e:
        await update.message.reply_text(f"💥 Erreur au lancement : {str(e)}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche les statistiques du dernier log généré par rclone."""
    if not await is_authorized(update): return
    log_path = "/var/log/backup/rclone.log"
    
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            # On récupère les 15 dernières lignes pour voir le résumé rclone
            last_lines = "".join(f.readlines()[-15:])
        await update.message.reply_text(f"📋 *Dernières infos du log :*\n```\n{last_lines}\n```", parse_mode='Markdown')
    else:
        await update.message.reply_text("⚠️ Aucun log trouvé. Attendez le premier backup.")

# --- DÉMARRAGE ---

if __name__ == '__main__':
    if not TOKEN or not AUTHORIZED_CHAT_ID:
        print("❌ Erreur critique : Variables d'environnement manquantes.")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping_remote))
    app.add_handler(CommandHandler("backup", run_backup))
    app.add_handler(CommandHandler("status", status_command))
    
    print("🚀 Bot en ligne...")
    app.run_polling()