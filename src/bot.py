import logging
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
from stripe_sdk import StripeSDK

load_dotenv(find_dotenv())

logging.basicConfig(level=logging.INFO)

stripe_sdk = StripeSDK(getenv("STRIPE_API_KEY"))
user_validator = UserValidator()


class CreateButtons:
    @staticmethod
    async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Creates an inline keyboard with all available products for the user to select.
        """
        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
        products = stripe_sdk.get_existing_products()
        logging.debug(f"{products=}", extra={"chat_id": update.effective_chat.id,
                      "user_id": update.effective_user.id, "function": "CreateButtons.list_products"})

        keyboard = [
            [
                InlineKeyboardButton(
                    f"{product.name}",
                    callback_data=f"select_product:{product.id}"
                )
            ]
            for product in products
        ]
        logging.debug(f"{keyboard=}", extra={"chat_id": update.effective_chat.id,
                      "user_id": update.effective_user.id, "function": "CreateButtons.list_products"})

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Choose a product:", reply_markup=reply_markup)


class HandleCommands:
    @staticmethod
    async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /help command by sending a help message to the user.
        """
        if not user_validator.user_can_access(update.effective_user.id):
            logging.debug("User not allowed to access the system.", extra={
                          "chat_id": update.effective_chat.id, "user_id": update.effective_user.id, "function": "HandleCommands.help"})
            return await update.message.reply_text("Sorry, you are not allowed to access the system.")

        await update.message.reply_text(
            "Hi, I am a bot that helps you create payment links for your products.\n"
            "You can use the following commands:\n\n"
            "/products - List all available products, click one of them to select it.\n"
            "/help - Show this help message.\n"
        )

    @staticmethod
    async def products(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /products command by listing all available products as inline keyboard
        """
        if not user_validator.user_can_access(update.effective_user.id):
            logging.debug("User not allowed to access the system.", extra={
                          "chat_id": update.effective_chat.id, "user_id": update.effective_user.id, "function": "HandleCommands.help"})
            return await update.message.reply_text("Sorry, you are not allowed to access the system.")

        await CreateButtons.list_products(update, context)


class HandleButtons:
    @staticmethod
    async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles button click events in the bot.
        The function processes the callback query data and performs actions based on the command received.
        """

        query = update.callback_query
        _command, _id = query.data.split(":", 1)
        logging.debug(f"{_command=}, {_id=}", extra={"chat_id": update.effective_chat.id,
                      "user_id": update.effective_user.id, "function": "HandleButtons.button_click"})

        if _command == HandleButtonsCommands.SELECT_PRODUCT:
            logging.debug("Selecting product...", extra={
                          "chat_id": update.effective_chat.id, "user_id": update.effective_user.id, "function": "HandleButtons.button_click"})
            return await HandleButtons.select_product(_id, update, context, query)

        else:
            logging.debug("Unknown command", extra={
                          "chat_id": update.effective_chat.id, "user_id": update.effective_user.id, "function": "HandleButtons.button_click"})
            await update.message.reply_text("Sorry, I could not understand that command.")

    @staticmethod
    async def select_product(product_id: str, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_query: CallbackQuery):
        """
        Handles the selection of a product by the user.
        """
        context.user_data[HandleMessagesCommands.SELECTED_PRODUCT] = product_id
        logging.debug(f"{product_id=}", extra={"chat_id": update.effective_chat.id,
                      "user_id": update.effective_user.id, "function": "HandleButtons.select_product"})

        await callback_query.edit_message_text("Enter the price for the product to create a new payment link:")


class HandleMessages:
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles incoming messages from the user.
        """
        print(update.effective_user.id)

        _user_data = context.user_data
        logging.debug(f"{_user_data=}", extra={"chat_id": update.effective_chat.id,
                      "user_id": update.effective_user.id, "function": "HandleMessages.handle"})

        if not user_validator.user_can_access(update.effective_user.id):
            logging.debug("User not allowed to access the system.", extra={
                          "chat_id": update.effective_chat.id, "user_id": update.effective_user.id, "function": "HandleCommands.help"})
            return await update.message.reply_text("Sorry, you are not allowed to access the system.")

        if _user_data.get(HandleMessagesCommands.SELECTED_PRODUCT) is not None:

            logging.debug("Creating payment link...", extra={
                          "chat_id": update.effective_chat.id, "user_id": update.effective_user.id, "function": "HandleMessages.handle"})
            await HandleMessages.handle_payment_link_creation(update, context)

        else:
            logging.debug("No product selected...", extra={
                          "chat_id": update.effective_chat.id, "user_id": update.effective_user.id, "function": "HandleMessages.handle"})
            await update.message.reply_text("To create a new payment link, please use the /products command to select a product.")

    @staticmethod
    async def handle_payment_link_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the creation of a new payment link for the selected product.
        """
        try:
            product_info = stripe.Product.retrieve(
                context.user_data[HandleMessagesCommands.SELECTED_PRODUCT])
            logging.debug(f"{product_info=}", extra={"chat_id": update.effective_chat.id,
                          "user_id": update.effective_user.id, "function": "HandleMessages.handle_payment_link_creation"})

            await update.message.reply_markdown(
                f"Creating a new payment link for the selected product: *{
                    product_info['name']}*.\n"
                "To change the product, please use the /products command and select a new one."
            )
            await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

            product_id = context.user_data[HandleMessagesCommands.SELECTED_PRODUCT]
            logging.debug(f"{product_id=}", extra={"chat_id": update.effective_chat.id,
                          "user_id": update.effective_user.id, "function": "HandleMessages.handle_payment_link_creation"})

            price = int(
                float(
                    re.sub(r'[^\d.]', '', update.message.text)
                )*100
            )
            logging.debug(f"{price=}", extra={"chat_id": update.effective_chat.id,
                          "user_id": update.effective_user.id, "function": "HandleMessages.handle_payment_link_creation"})

            # If the price already exists, retrieve the price ID, otherwise create a new price.
            price_id = next(
                (
                    price.id
                    for price in stripe_sdk.get_existing_prices(product_id)
                    if price.unit_amount == price
                ),
                None
            )
            logging.debug(f"{price_id=}", extra={"chat_id": update.effective_chat.id,
                          "user_id": update.effective_user.id, "function": "HandleMessages.handle_payment_link_creation"})

            if price_id:
                logging.debug("Price already exists, retrieving price data...", extra={
                              "chat_id": update.effective_chat.id, "user_id": update.effective_user.id, "function": "HandleMessages.handle_payment_link_creation"})
                price_data = stripe.Price.retrieve(price_id)

            else:
                logging.debug("Creating new price...", extra={
                              "chat_id": update.effective_chat.id, "user_id": update.effective_user.id, "function": "HandleMessages.handle_payment_link_creation"})
                price_id = stripe.Price.create(
                    currency="usd",
                    unit_amount=price,
                    product=context.user_data[HandleMessagesCommands.SELECTED_PRODUCT],
                ).id
                logging.debug(f"{price_id=}", extra={"chat_id": update.effective_chat.id,
                              "user_id": update.effective_user.id, "function": "HandleMessages.handle_payment_link_creation"})

                price_data = stripe.Price.retrieve(price_id)
                logging.debug(f"{price_data=}", extra={"chat_id": update.effective_chat.id,
                              "user_id": update.effective_user.id, "function": "HandleMessages.handle_payment_link_creation"})

            payment_link = stripe.PaymentLink.create(
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1
                    }
                ]
            )

            await update.message.reply_text(f"Payment link for ${(price_data['unit_amount']/100):,} ({price_data['currency']}) created:\n\n{payment_link['url']}")

        except Exception as e:
            logging.exception(e)
            await update.message.reply_text(f"Sorry, I could not create a new payment link. Please try again later.")
