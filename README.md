# Stripe Payments Links Bot

This project is a bot that generates Stripe payment links for your products or services.

## Features

- Generate Stripe payment links
- White and blacklisted users

## Requirements

- [Python >= 3.12.5](https://www.python.org/downloads/release/python-3125/)
- [Stripe Account](https://stripe.com/es-us)

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/Brixt18/StripePaymentsLinksBot
    ```
2. Navigate to the project directory:
    ```bash
    cd StripePaymentsLinksBot
    ```
3. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

### Environment Vars
1. Create a `.env` file in the root directory and add your Stripe API keys and configuration:
    ```env
    BOT_TOKEN=your_telegram_bot_token
    STRIPE_API_KEY=your_stripe_api_key
    ONLY_WHITELISTED=0  # This is a boolean value: 0 for False, 1 for True
    ```
> How to get Stripe's API Keys: [Stripe Docs](https://docs.stripe.com/keys)

> How to get Telegram Bot's Token: [Telegram Docs](https://core.telegram.org/bots/tutorial)

### Whitelisted users
To allow only whitelisted users, the `ONLY_WHITELISTED` environment variable must be set to `1`, and the Telegram user ID must be listed in `config/whitelist.csv`. If `ONLY_WHITELISTED` is set to `0`, the whitelist will have no effect.

### Blaclisted users
This list will always be checked before each user action. Add the user ID to `config/blacklist.csv` to block it from any further usage. No prior configuration is required.

## Usage


### Run the bot
1. Start the bot:
    ```bash
    python src/main.py
    ```

### Commands
- `/help` Displays a help message.
- `/products` Lists all your active products. Select one to create a payment link by typing the price, such as `10` or `99.98`.


## Contributing

1. Fork the repository.
2. Create a new branch:
    ```bash
    git checkout -b feature-branch
    ```
3. Make your changes and commit them:
    ```bash
    git commit -m "Description of changes"
    ```
4. Push to the branch:
    ```bash
    git push origin feature-branch
    ```
5. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or feedback, please open an issue or contact the repository owner.
