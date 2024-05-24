import logging
from telegram import Update, Bot, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests

API_TOKEN = 'YOUR_BOT_API_TOKEN'

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define command handlers
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hi! Send me some tags and I will find podcasts for you. Type /help for more commands.')

def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "Here are the available commands:\n"
        "/start - Start interacting with the bot\n"
        "/help - Get help on how to use the bot\n"
        "/top <category> - Get the top podcasts in a specific category (e.g., /top technology)\n"
        "Or simply send me some tags and I will find podcasts for you!"
    )
    update.message.reply_text(help_text)

def get_podcasts(tags):
    url = 'https://itunes.apple.com/search'
    params = {
        'term': tags,
        'media': 'podcast',
        'limit': 5
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

def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(API_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("top", top_command))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Log all errors
    dispatcher.add_error_handler(lambda update, context: logger.warning(f'Update "{update}" caused error "{context.error}"'))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT.
    updater.idle()

if __name__ == '__main__':
    main()
