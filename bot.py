import logging
import datetime
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, JobQueue
import requests
import json
import os

API_TOKEN = '7025435221:AAFEY838oCP45vZR6Ab8xsWls1XDzKA_lTU'
SUBSCRIPTIONS_FILE = 'subscriptions.json'

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load subscriptions from file
def load_subscriptions():
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save subscriptions to file
def save_subscriptions(subscriptions):
    with open(SUBSCRIPTIONS_FILE, 'w') as f:
        json.dump(subscriptions, f)

# Initialize subscriptions
subscriptions = load_subscriptions()

# Define command handlers
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hi! Send me some tags and I will find podcasts for you. Type /help for more commands.')

def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "Here are the available commands:\n"
        "/start - Start interacting with the bot\n"
        "/help - Get help on how to use the bot\n"
        "/top <category> - Get the top podcasts in a specific category (e.g., /top technology)\n"
        "/subscribe <tags> - Subscribe to daily podcast updates (e.g., /subscribe technology, AI)\n"
        "/unsubscribe <tags> - Unsubscribe from daily podcast updates (e.g., /unsubscribe technology, AI)\n"
        "/list - List your current subscriptions\n"
        "Or simply send me some tags and I will find podcasts for you!"
    )
    update.message.reply_text(help_text)

def get_podcasts(tags):
    url = 'https://itunes.apple.com/search'
    params = {
        'term': tags,
        'media': 'podcast',
        'limit': 20
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('results', [])
    else:
        return []

def get_top_podcasts(category):
    url = 'https://itunes.apple.com/search'
    params = {
        'term': category,
        'media': 'podcast',
        'limit': 5
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('results', [])
    else:
        return []

def handle_message(update: Update, context: CallbackContext) -> None:
    tags = update.message.text
    podcasts = get_podcasts(tags)
    if podcasts:
        reply = "\n\n".join([f"*Title*: {podcast['collectionName']}\n*Description*: {podcast.get('description', 'No description available.')}\n[Listen here]({podcast['collectionViewUrl']})" for podcast in podcasts])
    else:
        reply = "Sorry, I couldn't find any podcasts for the given tags."
    update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

def top_command(update: Update, context: CallbackContext) -> None:
    if len(context.args) == 0:
        update.message.reply_text('Please specify a category (e.g., /top technology).')
        return

    category = ' '.join(context.args)
    podcasts = get_top_podcasts(category)
    if podcasts:
        reply = "\n\n".join([f"*Title*: {podcast['collectionName']}\n*Description*: {podcast.get('description', 'No description available.')}\n[Listen here]({podcast['collectionViewUrl']})" for podcast in podcasts])
    else:
        reply = f"Sorry, I couldn't find any top podcasts for the category '{category}'."
    update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

def subscribe(update: Update, context: CallbackContext) -> None:
    if len(context.args) == 0:
        update.message.reply_text('Please specify tags to subscribe (e.g., /subscribe technology, AI).')
        return

    user_id = str(update.message.from_user.id)
    tags = ' '.join(context.args)

    if user_id not in subscriptions:
        subscriptions[user_id] = []
    if tags not in subscriptions[user_id]:
        subscriptions[user_id].append(tags)
        save_subscriptions(subscriptions)
        update.message.reply_text(f'Subscribed to daily updates for tags: {tags}')
    else:
        update.message.reply_text(f'You are already subscribed to tags: {tags}')

def unsubscribe(update: Update, context: CallbackContext) -> None:
    if len(context.args) == 0:
        update.message.reply_text('Please specify tags to unsubscribe (e.g., /unsubscribe technology, AI).')
        return

    user_id = str(update.message.from_user.id)
    tags = ' '.join(context.args)

    if user_id in subscriptions and tags in subscriptions[user_id]:
        subscriptions[user_id].remove(tags)
        if not subscriptions[user_id]:
            del subscriptions[user_id]
        save_subscriptions(subscriptions)
        update.message.reply_text(f'Unsubscribed from daily updates for tags: {tags}')
    else:
        update.message.reply_text(f'You are not subscribed to tags: {tags}')

def list_subscriptions(update: Update, context: CallbackContext) -> None:
    user_id = str(update.message.from_user.id)

    if user_id in subscriptions and subscriptions[user_id]:
        reply = "Your current subscriptions:\n" + "\n".join(subscriptions[user_id])
    else:
        reply = "You have no subscriptions."
    update.message.reply_text(reply)

def daily_update(context: CallbackContext) -> None:
    for user_id, tags_list in subscriptions.items():
        for tags in tags_list:
            podcasts = get_podcasts(tags)
            if podcasts:
                reply = "\n\n".join([f"*Title*: {podcast['collectionName']}\n*Description*: {podcast.get('description', 'No description available.')}\n[Listen here]({podcast['collectionViewUrl']})" for podcast in podcasts])
                context.bot.send_message(chat_id=user_id, text=reply, parse_mode=ParseMode.MARKDOWN)

def main() -> None:
    updater = Updater(API_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    job_queue = updater.job_queue

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("top", top_command))
    dispatcher.add_handler(CommandHandler("subscribe", subscribe))
    dispatcher.add_handler(CommandHandler("unsubscribe", unsubscribe))
    dispatcher.add_handler(CommandHandler("list", list_subscriptions))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    job_queue.run_daily(daily_update, time=datetime.time(hour=8, minute=0, second=0))

    dispatcher.add_error_handler(lambda update, context: logger.warning(f'Update "{update}" caused error "{context.error}"'))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
