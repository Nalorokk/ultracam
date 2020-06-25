from pprint import pprint
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import shared

bot = None


def initBot():
    global bot
    if 'tg_token' in shared.config:
        bot = telegram.Bot(token=shared.config['tg_token'])

initBot()


def echo(bot, update):
    """Echo the user message."""
    print('Recieved msg '+update.message.text+' from '+str(update.effective_user.id)+' in chat: '+str(update.effective_chat.id))


def begin():
    updater = Updater(bot.token)

    dp = updater.dispatcher
    

    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.

    return updater

if __name__ == "__main__":
    updater = begin()
    updater.idle()
