import logging
from os import getenv

from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          MessageHandler, filters)

from bot import HandleButtons, HandleCommands, HandleMessages


def main():
    logging.info("Building bot")
    app = (
        Application.builder()
        .token(getenv("BOT_TOKEN"))
        .build()
    )

    app.add_handler(CommandHandler("products", HandleCommands.products))
    app.add_handler(CommandHandler("help", HandleCommands.help))
    app.add_handler(CommandHandler("clear", HandleCommands.clear))
    app.add_handler(CommandHandler("start", HandleCommands.start))
    app.add_handler(CallbackQueryHandler(HandleButtons.button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, HandleMessages.handle))  # noqa

    logging.info("Bot is Running")
    app.run_polling()


if __name__ == "__main__":
    main()
