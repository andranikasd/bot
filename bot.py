import logging
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests

# Replace 'YOUR_BOT_API_TOKEN' with your actual bot API token
API_TOKEN = '7025435221:AAFEY838oCP45vZR6Ab8xsWls1XDzKA_lTU'

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define a command handler. This usually takes the two arguments update and context.
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hi! Send me some tags and I will find podcasts for you.')

def get_podcasts(tags):
    url = 'https://itunes.apple.com/search'
    params = {
        'term': tags,
        'media': 'podcast',
        'limit': 5  # Limit the number of results to 5 for simplicity
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
        reply = "\n\n".join([f"Title: {podcast['collectionName']}\nDescription: {podcast.get('description', 'No description available.')}\nLink: {podcast['collectionViewUrl']}" for podcast in podcasts])
    else:
        reply = "Sorry, I couldn't find any podcasts for the given tags."
    update.message.reply_text(reply)

def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(API_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT.
    updater.idle()

if __name__ == '__main__':
    main()
