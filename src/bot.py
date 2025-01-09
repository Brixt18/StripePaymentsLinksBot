import stripe.error
from helpers.logger import setup_logger
import re
from os import getenv

import stripe
from dotenv import find_dotenv, load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram._callbackquery import CallbackQuery
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from helpers.user_validator import UserValidator
from models.enums import HandleButtonsCommands, HandleMessagesCommands
from helpers.stripe_sdk import StripeSDK
from stripe import StripeError

load_dotenv(find_dotenv())
logging = setup_logger()
stripe_sdk = StripeSDK(getenv("STRIPE_API_KEY"))
user_validator = UserValidator()


class CreateButtons:
    @staticmethod
    async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Creates an inline keyboard with all available products for the user to select.
        """
        logging.info("Creating products to list as buttons", extra={"chat_id": update.effective_chat.id, "user_id": update.effective_user.id})  # noqa

        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
        products = stripe_sdk.get_existing_products(active=True)

        keyboard = [
            [
                InlineKeyboardButton(
                    f"{product.name}",
                    callback_data=f"select_product:{product.id}"
                )
            ]
            for product in products
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Choose a product:", reply_markup=reply_markup)


class HandleCommands:
    @staticmethod
    async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /help command by sending a help message to the user.
        """
        logging.info("Handling /help command", extra={"chat_id": update.effective_chat.id, "user_id": update.effective_user.id})  # noqa

        if not user_validator.user_can_access(update.effective_user.id):
            return await update.message.reply_text("Sorry, you are not allowed to access the system.")

        await update.message.reply_text(
            "Hi, I am a bot that helps you create payment links for your products.\n"
            "You can use the following commands:\n\n"
            "/products - List all available products, click one of them to select it.\n"
            "/help - Show this help message.\n"
            "/clear - Clear the user data.\n"
            "/start - Start the bot and show a welcome message.\n"
        )

    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /start command by sending a welcome message to the user.
        """
        logging.info("Handling /start command", extra={"chat_id": update.effective_chat.id, "user_id": update.effective_user.id})

        if not user_validator.user_can_access(update.effective_user.id):
            return await update.message.reply_text("Sorry, you are not allowed to access the system.")
        
        await update.message.reply_text("Welcome to the payment link bot. Use the /help command to see the available commands.")

    @staticmethod
    async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /clear command by clearing the user data.
        """
        logging.info("Handling /clear command", extra={"chat_id": update.effective_chat.id, "user_id": update.effective_user.id})

        context.user_data[HandleMessagesCommands.SELECTED_PRODUCT] = None
        await update.message.reply_text("User data cleared.")

    @staticmethod
    async def products(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /products command by listing all available products as inline keyboard
        """
        logging.info("Handling /products command", extra={"chat_id": update.effective_chat.id, "user_id": update.effective_user.id})  # noqa

        if not user_validator.user_can_access(update.effective_user.id):
            return await update.message.reply_text("Sorry, you are not allowed to access the system.")

        await CreateButtons.list_products(update, context)


class HandleButtons:
    @staticmethod
    async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles button click events in the bot.
        The function processes the callback query data and performs actions based on the command received.
        """
        logging.info("Handling clicked button", extra={"chat_id": update.effective_chat.id, "user_id": update.effective_user.id})  # noqa

        query = update.callback_query

        _command, _id = query.data.split(":", 1)
        logging.debug(f"{_command=}, {_id=}")

        if _command == HandleButtonsCommands.SELECT_PRODUCT:
            return await HandleButtons.select_product(_id, update, context, query)

        else:
            logging.warning("Unknown command received", extra={"chat_id": update.effective_chat.id, "user_id": update.effective_user.id})
            await update.message.reply_text("Sorry, I could not understand that command.")

    @staticmethod
    async def select_product(product_id: str, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_query: CallbackQuery):
        """
        Handles the selection of a product by the user.
        """
        logging.info("Handling select product from button", extra={"chat_id": update.effective_chat.id, "user_id": update.effective_user.id})  # noqa

        context.user_data[HandleMessagesCommands.SELECTED_PRODUCT] = product_id
        logging.debug(f"{product_id=}")

        await callback_query.edit_message_text("Enter the price for the product to create a new payment link:")


class HandleMessages:
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles incoming messages from the user.
        """
        logging.info("Handling messages", extra={"chat_id": update.effective_chat.id, "user_id": update.effective_user.id})  # noqa

        _user_data = context.user_data

        if not user_validator.user_can_access(update.effective_user.id):
            return await update.message.reply_text("Sorry, you are not allowed to access the system.")

        if _user_data.get(HandleMessagesCommands.SELECTED_PRODUCT) is not None:
            await HandleMessages.handle_payment_link_creation(update, context)

        else:
            await update.message.reply_text("To create a new payment link, please use the /products command to select a product.")

    @staticmethod
    async def handle_payment_link_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the creation of a new payment link for the selected product.
        """
        logging.info("Creating payment link", extra={"chat_id": update.effective_chat.id, "user_id": update.effective_user.id, "function": "HandleMessages.handle_payment_link_creation"})  # noqa

        try:
            product_info = stripe.Product.retrieve(context.user_data[HandleMessagesCommands.SELECTED_PRODUCT])  # noqa
            logging.debug(f"{product_info=}")

            await update.message.reply_markdown(
                f"Creating a new payment link for the selected product: *{product_info['name']}*.\n"  # noqa
                "To change the product, please use the /products command and select a new one."
            )
            await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

            product_id = context.user_data[HandleMessagesCommands.SELECTED_PRODUCT]
            logging.debug(f"{product_id=}")

            try:
                price = int(
                    float(
                        re.sub(r'[^\d.]', '', update.message.text)
                    )*100
                )

            except ValueError:
                return await update.message.reply_text("Sorry, I could not understand the price. Please enter a valid number.")
            
            logging.debug(f"{price=}")

            # If the price already exists, retrieve the price ID, otherwise create a new price.
            price_id = next(
                (
                    price.id
                    for price in stripe_sdk.get_existing_prices(product_id)
                    if price.unit_amount == price
                ),
                None
            )
            logging.debug(f"{price_id=}")

            if price_id:
                logging.info("Price already exists, retrieving price data", extra={"chat_id": update.effective_chat.id, "user_id": update.effective_user.id})
                price_data = stripe.Price.retrieve(price_id)

            else:
                logging.info("Creating new price", extra={"chat_id": update.effective_chat.id, "user_id": update.effective_user.id})
                
                try:
                    price_id = stripe.Price.create(
                        currency="usd",
                        unit_amount=price,
                        product=context.user_data[HandleMessagesCommands.SELECTED_PRODUCT],
                    ).id
                
                except StripeError as e:
                    _error = str(e)
                    if "Invalid integer" in _error:
                        return await update.message.reply_text("Sorry, the price is invalid. Please enter a lower value.")

                    raise e

                logging.debug(f"{price_id=}")

                price_data = stripe.Price.retrieve(price_id)
                logging.debug(f"{price_data=}")

            logging.debug("Creating payment link")

            try:
                payment_link = stripe.PaymentLink.create(
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1
                    }
                ]
            )
            
            except StripeError as e:
                _error = str(e)
                if "The Checkout Session's total amount must convert to at least" in _error:
                    return await update.message.reply_text("Sorry, the price is too low to create a payment link.")

                raise e
            
            logging.debug(f"{payment_link=}")

            await update.message.reply_text(f"Payment link for ${(price_data['unit_amount']/100):,} ({price_data['currency']}) created:\n\n{payment_link['url']}")

        except Exception as e:
            logging.exception(e)
            await update.message.reply_text(f"Sorry, I could not create a new payment link. Please try again later.")
