# Gift Price Bot

A Telegram bot that fetches the price of a Telegram Gift (NFT) from multiple markets and displays them in different currencies.

## Features

- Fetches gift prices from three markets: Tonnel, Portals, and MRKT.
- Displays prices in TON, USD, and IRR.
- Easy to use with simple commands.
- Can be added to groups.

## Installation & Usage (Docker)

**You do not need to install Python.** You only need [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/).

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/thegbu/Gift-Price gift-price/ && cd gift-price
    ```

2.  **Configuration:**
    Open `.env` file and edit it:
    - `BOT_TOKEN`: Your Telegram bot token from @BotFather.
    - `API_ID` and `API_HASH`: Your Telegram API credentials from my.telegram.org.
    - `CHANNEL_NAME` and `CHANNEL_URL` (Optional).
    - `TONNEL_URL`, `PORTALS_URL`, `MRKT_URL` (Optional).

3.  **Generate Sessions:**
    Run this command to log in to Telegram and generate the session files. This runs inside a temporary container:
    ```bash
    docker compose run --rm gift-price-bot python generate_sessions.py
    ```
    Follow the on-screen prompts to log in. The session files will be saved to the `markets/` directory.

4.  **Run the Bot:**
    Start the bot in the background:
    ```bash
    docker compose up -d
    ```

5.  **Manage the Bot:**
    - **View Logs:** `docker compose logs -f`
    - **Stop:** `docker compose down`
    - **Restart:** `docker compose restart`

## Legacy Installation (Local Python)

If you prefer to run the bot without Docker, follow these steps:

1.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Linux:
    source venv/bin/activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Generate Sessions:**
    ```bash
    python generate_sessions.py
    ```

4.  **Run the bot:**
    ```bash
    python main.py
    ```

## Usage

1. **Start the bot:**
   Send `/start` or `/help` to the bot to see the welcome message.

2. **Check Prices:**
   - **Direct Link:** Send the gift link directly to the bot:
     `/p https://t.me/nft/gift-name`
   - **Reply Mode:** Reply to a message containing a gift link with `/p`.

   The bot will reply with prices from Tonnel, Portals, and MRKT.
