# Gift Price Bot

A Telegram bot that fetches the price of a Telegram Gift (NFT) from multiple markets and displays them in different currencies.

## Features

- Fetches gift prices from three markets: Tonnel, Portals, and MRKT.
- Displays prices in TON, USD, and IRR.
- Easy to use with simple commands.
- Can be added to groups.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/thegbu/Gift-Price gift-price/ && cd gift-price
   ```

2. **Create a virtual environment:**
   - **Windows:**
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```
     To deactivate the virtual environment later, simply run `deactivate`.

   - **Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
     To deactivate the virtual environment later, simply run `deactivate`.

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Open `.env` file and edit it**

   - `BOT_TOKEN`: Your Telegram bot token from @BotFather.
   - `API_ID` and `API_HASH`: Your Telegram API credentials from my.telegram.org.
   - `CHANNEL_NAME` and `CHANNEL_URL` are optional. If you provide them, the bot will display a button with your channel's name and link.
   - `TONNEL_URL`, `PORTALS_URL`, `MRKT_URL`: These are optional referral links for the markets. If provided, the market names in the bot's response will link to these URLs. If omitted, the names will be displayed as plain text.

2. **Generate the Pyrogram sessions:**

   Run the following command to generate the `portals.session` and `mrkt.session` files:

   ```bash
   python3 generate_sessions.py
   ```

   To use MRKT and Portals, you need to log in with a Telegram account that has already started both bots. Therefore, after running `generate_sessions.py`, you will be required to log in to the same account twice.

## Usage

1. **Run the bot:**
   ```bash
   python3 main.py
   ```

2. **Use the commands:**
   - `/start` or `/help`: Displays a welcome message.
   - `/p` or `/price`: Fetches the price of a gift.

   You can use the `/p` or `/price` command in two ways:
   - Send the command with a link: `/p https://t.me/nft/...`
   - Reply to a message that contains a link with just the command: `/p`

## Running in the Background (Deployment)

To keep the bot running 24/7 on a server, you should run it inside a terminal multiplexer like `tmux` or `screen`. This will prevent the bot from stopping when you close your SSH session.

### Using `tmux`

1.  Start a new `tmux` session:
    ```bash
    tmux new -s gift-bot
    ```
2.  Run the bot:
    ```bash
    python3 main.py
    ```
3.  Detach from the session by pressing `Ctrl+b` then `d`. The bot will continue running.
4.  To re-attach to the session later, use: `tmux attach -t gift-bot`

### Using `screen`

1.  Start a new `screen` session:
    ```bash
    screen -S gift-bot
    ```
2.  Run the bot:
    ```bash
    python3 main.py
    ```
3.  Detach from the session by pressing `Ctrl+a` then `d`.
4.  To re-attach to the session later, use: `screen -r gift-bot`
